#!/usr/bin/env python3
"""One-off, local-only Phase 1 hardware and Ollama viability probe.

This is evidence collection for preliminary hardware validation, not the
production benchmark runner and not a benchmark scorer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import socket
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = ROOT / "evidence" / "phase1-theimp-2026-07-31"
EVIDENCE = DEFAULT_EVIDENCE
PROFILE_ID = "theimp-2026-07-31"
OLLAMA = "http://127.0.0.1:11434"
NUM_CTX = 4096
SCORED_TIMEOUT_SECONDS = 120


PROBES: list[dict[str, Any]] = [
    {
        "id": "extraction",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["customer_id", "priority", "refund_requested"],
            "properties": {
                "customer_id": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                "refund_requested": {"type": "boolean"},
            },
        },
        "prompt": (
            "Return only JSON matching the supplied schema. Extract the facts from this message; "
            "do not infer missing facts. Message: Customer C-1042 says the duplicate $27 charge "
            "must be refunded today and marks the issue high priority."
        ),
    },
    {
        "id": "classification",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["route", "needs_review"],
            "properties": {
                "route": {"type": "string", "enum": ["billing", "sales", "technical"]},
                "needs_review": {"type": "boolean"},
            },
        },
        "prompt": (
            "Return only JSON matching the supplied schema. Route this ticket. Ticket: "
            "The invoice lists two seats but our contract has one; a person should verify it."
        ),
    },
    {
        "id": "normalization",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["date", "amount", "currency"],
            "properties": {
                # Ollama 0.32.5's grammar converter rejects the equivalent \d escape.
                "date": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"},
                "amount": {"type": "number"},
                "currency": {"type": "string", "enum": ["USD", "EUR", "GBP"]},
            },
        },
        "prompt": (
            "Return only JSON matching the supplied schema. Normalize: On July 4, 2026, "
            "the customer paid one thousand two hundred thirty-four US dollars and fifty cents."
        ),
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command(argv: list[str], timeout: int = 30) -> dict[str, Any]:
    started = utc_now()
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return {
            "argv": argv,
            "started_at": started,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"argv": argv, "started_at": started, "error": repr(exc)}


def api(path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if data is None else "POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    with Path("/proc/meminfo").open(encoding="utf-8") as handle:
        for line in handle:
            key, raw = line.split(":", 1)
            match = re.search(r"(\d+)", raw)
            if match:
                values[key] = int(match.group(1)) * 1024
    return values


class MemorySampler:
    def __init__(self) -> None:
        self.samples: list[dict[str, Any]] = []
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self) -> None:
        while not self.stop_event.is_set():
            values = meminfo()
            self.samples.append(
                {
                    "timestamp": utc_now(),
                    "mem_available_bytes": values.get("MemAvailable"),
                    "swap_free_bytes": values.get("SwapFree"),
                }
            )
            self.stop_event.wait(0.1)

    def __enter__(self) -> "MemorySampler":
        self.thread.start()
        return self

    def __exit__(self, *_: Any) -> None:
        self.stop_event.set()
        self.thread.join()


def simple_schema_check(value: Any, schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["top-level value is not an object"]
    properties = schema["properties"]
    if set(value) != set(schema["required"]):
        errors.append(f"keys {sorted(value)} do not exactly match required keys {sorted(schema['required'])}")
    for key, rule in properties.items():
        if key not in value:
            continue
        item = value[key]
        expected = rule["type"]
        valid_type = {
            "string": isinstance(item, str),
            "boolean": isinstance(item, bool),
            "number": isinstance(item, (int, float)) and not isinstance(item, bool),
        }[expected]
        if not valid_type:
            errors.append(f"{key} is not {expected}")
            continue
        if "enum" in rule and item not in rule["enum"]:
            errors.append(f"{key} is outside enum")
        if "pattern" in rule and not re.fullmatch(rule["pattern"], item):
            errors.append(f"{key} does not match pattern")
    return errors


def model_metadata(model: str) -> dict[str, Any]:
    tags = api("/api/tags")["models"]
    tag = next(item for item in tags if item["name"] == model)
    show = api("/api/show", {"model": model})
    model_info = show.get("model_info", {})
    context = {key: value for key, value in model_info.items() if key.endswith("context_length")}
    return {
        "tag_record": tag,
        "details": show.get("details"),
        "capabilities": show.get("capabilities"),
        "default_parameters": show.get("parameters"),
        "native_context_fields": context,
        "modified_at": show.get("modified_at"),
    }


def run_request(model: str, probe: dict[str, Any], timeout: int) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": probe["prompt"]}],
        "stream": False,
        "think": False,
        "format": probe["schema"],
        "keep_alive": "10m",
        "options": {
            "temperature": 0,
            "seed": 42,
            "num_ctx": NUM_CTX,
            "num_predict": 256,
        },
    }
    started_at = utc_now()
    start = time.monotonic()
    error: dict[str, Any] | None = None
    response: dict[str, Any] | None = None
    with MemorySampler() as sampler:
        try:
            response = api("/api/chat", payload, timeout=timeout)
        except urllib.error.HTTPError as exc:
            error = {
                "type": type(exc).__name__,
                "message": str(exc),
                "status": exc.code,
                "response_body": exc.read().decode("utf-8", errors="replace"),
            }
        except Exception as exc:  # Preserve the exact operational failure.
            error = {"type": type(exc).__name__, "message": str(exc)}
    elapsed = time.monotonic() - start
    available = [item["mem_available_bytes"] for item in sampler.samples if item["mem_available_bytes"]]
    parsed: Any = None
    parse_error: str | None = None
    schema_errors: list[str] = []
    if response is not None:
        raw = response.get("message", {}).get("content", "")
        try:
            parsed = json.loads(raw)
            schema_errors = simple_schema_check(parsed, probe["schema"])
        except json.JSONDecodeError as exc:
            parse_error = str(exc)
    eval_count = response.get("eval_count") if response else None
    eval_duration = response.get("eval_duration") if response else None
    throughput = None
    if eval_count is not None and eval_duration:
        throughput = eval_count / (eval_duration / 1_000_000_000)
    return {
        "started_at": started_at,
        "completed_at": utc_now(),
        "request": payload,
        "response": response,
        "error": error,
        "wall_latency_seconds": elapsed,
        "timed_out": isinstance(error, dict) and error.get("type") in {"TimeoutError", "URLError"} and elapsed >= timeout,
        "output_tokens": eval_count,
        "warm_output_tokens_per_second": throughput,
        "strict_json_parse_ok": parsed is not None and parse_error is None,
        "schema_check_ok": parsed is not None and not schema_errors,
        "parse_error": parse_error,
        "schema_errors": schema_errors,
        "memory": {
            "sample_count": len(sampler.samples),
            "minimum_mem_available_bytes": min(available) if available else None,
            "starting_mem_available_bytes": available[0] if available else None,
            "maximum_observed_available_drop_bytes": (available[0] - min(available)) if available else None,
            "samples": sampler.samples,
        },
    }


def unload(model: str) -> dict[str, Any]:
    try:
        return api("/api/generate", {"model": model, "prompt": "", "keep_alive": 0}, timeout=30)
    except Exception as exc:
        return {"error": {"type": type(exc).__name__, "message": str(exc)}}


def capture_hardware() -> None:
    commands = {
        "hostname": ["hostname"],
        "uname": ["uname", "-a"],
        "os_release": ["sed", "-n", "1,40p", "/etc/os-release"],
        "lscpu": ["lscpu"],
        "free": ["free", "-h"],
        "swapon": ["swapon", "--show", "--bytes"],
        "lsblk": ["lsblk", "-o", "NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS,MODEL"],
        "df": ["df", "-hT"],
        "lspci": ["lspci", "-nnk"],
        "nvidia_smi": ["nvidia-smi"],
        "python": ["python3", "--version"],
        "node": ["node", "--version"],
        "docker": ["docker", "--version"],
        "git": ["git", "--version"],
        "ollama_version": ["ollama", "--version"],
        "ollama_list": ["ollama", "list"],
        "ollama_ps": ["ollama", "ps"],
        "ollama_service_active": ["systemctl", "is-active", "ollama"],
        "ollama_service_status": ["systemctl", "status", "ollama", "--no-pager"],
        "git_status": ["git", "status", "--short"],
        "git_commit": ["git", "rev-parse", "HEAD"],
    }
    record = {
        "profile_id": PROFILE_ID,
        "captured_at": utc_now(),
        "hostname_python": socket.gethostname(),
        "platform_python": platform.platform(),
        "working_directory": str(ROOT),
        "commands": {name: command(argv) for name, argv in commands.items()},
        "ollama_api_version": api("/api/version"),
        "ollama_api_tags": api("/api/tags"),
    }
    write_json(EVIDENCE / "hardware-runtime-profile.raw.json", record)


def capture_runtime_state(label: str) -> None:
    commands = {
        "hostname": ["hostname"],
        "uname": ["uname", "-a"],
        "ollama_binary_path": ["readlink", "-f", "/usr/local/bin/ollama"],
        "ollama_binary_and_service_checksums": [
            "sha256sum",
            "/usr/local/bin/ollama",
            "/etc/systemd/system/ollama.service",
            "/etc/systemd/system/ollama.service.d/override.conf",
        ],
        "ollama_binary_and_service_stats": [
            "stat",
            "-c",
            "%n %s bytes %U:%G %a %y",
            "/usr/local/bin/ollama",
            "/etc/systemd/system/ollama.service",
            "/etc/systemd/system/ollama.service.d/override.conf",
        ],
        "ollama_client_version": ["ollama", "--version"],
        "ollama_list": ["ollama", "list"],
        "ollama_ps": ["ollama", "ps"],
        "ollama_service_show": [
            "systemctl",
            "show",
            "ollama",
            "--no-pager",
            "-p",
            "FragmentPath",
            "-p",
            "DropInPaths",
            "-p",
            "User",
            "-p",
            "Group",
            "-p",
            "Environment",
            "-p",
            "ExecStart",
            "-p",
            "ActiveState",
            "-p",
            "UnitFileState",
        ],
        "ollama_service_cat": ["systemctl", "cat", "ollama", "--no-pager"],
        "ollama_service_status": ["systemctl", "status", "ollama", "--no-pager", "--full"],
        "ollama_service_active": ["systemctl", "is-active", "ollama"],
        "ollama_service_enabled": ["systemctl", "is-enabled", "ollama"],
        "model_storage_stat": [
            "stat",
            "-c",
            "%n %s bytes %U:%G %a %y",
            "/usr/share/ollama/.ollama/models",
        ],
        "model_storage_size": ["du", "-sh", "/usr/share/ollama/.ollama/models"],
        "filesystem_bytes": ["df", "-B1", "/", "/usr/local", "/usr/share/ollama/.ollama/models"],
        "filesystem_human": ["df", "-h", "/", "/usr/local", "/usr/share/ollama/.ollama/models"],
        "nvidia_smi": ["nvidia-smi"],
        "nvidia_proc_version": ["sed", "-n", "1,80p", "/proc/driver/nvidia/version"],
        "nvidia_proc_gpu": [
            "sed",
            "-n",
            "1,80p",
            "/proc/driver/nvidia/gpus/0000:01:00.0/information",
        ],
        "nvidia_module_version": ["/usr/sbin/modinfo", "-F", "version", "nvidia"],
        "nvidia_userspace_libraries": ["/sbin/ldconfig", "-p"],
        "nvidia_packages": [
            "dpkg-query",
            "-W",
            "-f=${Package}\\t${Version}\\t${Status}\\n",
            "nvidia*",
            "libnvidia*",
        ],
        "nvidia_package_policy": [
            "apt-cache",
            "policy",
            "nvidia-driver-590-open",
            "nvidia-driver-595-open",
            "nvidia-utils-590",
            "nvidia-utils-595",
            "libnvidia-compute-590",
            "libnvidia-compute-595",
        ],
        "git_status": ["git", "status", "--short"],
        "git_commit": ["git", "rev-parse", "HEAD"],
        "initialprompt_checksum": ["sha256sum", "initialprompt.md"],
    }
    record = {
        "evidence_type": "phase1_runtime_upgrade_state",
        "label": label,
        "profile_id": PROFILE_ID,
        "captured_at": utc_now(),
        "working_directory": str(ROOT),
        "commands": {name: command(argv) for name, argv in commands.items()},
        "ollama_api_version": api("/api/version"),
        "ollama_api_tags": api("/api/tags"),
        "ollama_api_ps": api("/api/ps"),
    }
    write_json(EVIDENCE / f"runtime-{label}.raw.json", record)


def capture_upgrade_provenance() -> None:
    release_path = Path("/tmp/goodenough-ollama-latest-release.json")
    release = json.loads(release_path.read_text(encoding="utf-8")) if release_path.exists() else None
    record = {
        "evidence_type": "ollama_runtime_upgrade_provenance",
        "captured_at": utc_now(),
        "profile_id": PROFILE_ID,
        "official_sources": {
            "installer": "https://ollama.com/install.sh",
            "release": "https://github.com/ollama/ollama/releases/tag/v0.32.5",
            "archive": "https://ollama.com/download/ollama-linux-amd64.tar.zst?version=0.32.5",
        },
        "official_release_metadata": (
            {
                "tag_name": release.get("tag_name"),
                "name": release.get("name"),
                "published_at": release.get("published_at"),
                "html_url": release.get("html_url"),
                "asset": next(
                    (
                        {
                            "name": item.get("name"),
                            "size": item.get("size"),
                            "digest": item.get("digest"),
                            "browser_download_url": item.get("browser_download_url"),
                            "updated_at": item.get("updated_at"),
                        }
                        for item in release.get("assets", [])
                        if item.get("name") == "ollama-linux-amd64.tar.zst"
                    ),
                    None,
                ),
            }
            if release
            else None
        ),
        "downloaded_sources": {
            "installer": command(["sha256sum", "/tmp/goodenough-ollama-install.sh"]),
            "release_metadata": command(["sha256sum", str(release_path)]),
            "archive": command(
                ["sha256sum", "/tmp/goodenough-ollama-linux-amd64-v0.32.5.tar.zst"]
            ),
            "archive_stat": command(
                [
                    "stat",
                    "-c",
                    "%n %s bytes %U:%G %a %y",
                    "/tmp/goodenough-ollama-linux-amd64-v0.32.5.tar.zst",
                ]
            ),
        },
        "installed_runtime": command(
            [
                "stat",
                "-c",
                "%n %s bytes %U:%G %a %y",
                "/usr/local/bin/ollama",
                "/usr/local/lib/ollama",
            ]
        ),
        "preserved_runtime_backups": command(
            [
                "stat",
                "-c",
                "%n %s bytes %U:%G %a %y",
                "/usr/local/bin/ollama-0.17.4-backup",
                "/usr/local/lib/ollama-0.17.4-backup",
            ]
        ),
        "service_configuration_checksums": command(
            [
                "sha256sum",
                "/etc/systemd/system/ollama.service",
                "/etc/systemd/system/ollama.service.d/override.conf",
            ]
        ),
        "model_storage": command(
            ["stat", "-c", "%n %U:%G %a %y", "/usr/share/ollama/.ollama/models"]
        ),
        "ollama_api_version": api("/api/version"),
        "ollama_api_tags": api("/api/tags"),
    }
    write_json(EVIDENCE / "upgrade-provenance.raw.json", record)


def capture_nvidia_diagnosis() -> None:
    module_path = f"/lib/modules/{platform.release()}/updates/dkms/nvidia.ko.zst"
    commands = {
        "nvidia_smi": ["nvidia-smi"],
        "loaded_module_sysfs_version": ["sed", "-n", "1,20p", "/sys/module/nvidia/version"],
        "loaded_module_proc_version": ["sed", "-n", "1,80p", "/proc/driver/nvidia/version"],
        "installed_module_version": ["/usr/sbin/modinfo", "-F", "version", module_path],
        "installed_module_vermagic": ["/usr/sbin/modinfo", "-F", "vermagic", module_path],
        "installed_module_stat": ["stat", "-c", "%n %s bytes %y", module_path],
        "dkms_status": ["/usr/sbin/dkms", "status"],
        "userspace_nvml_target": [
            "readlink",
            "-f",
            "/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1",
        ],
        "userspace_nvml_stat": [
            "stat",
            "-c",
            "%n %s bytes %y",
            "/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.595.84",
        ],
        "nvidia_packages": [
            "dpkg-query",
            "-W",
            "-f=${Package}\\t${Version}\\t${Status}\\n",
            "nvidia*",
            "libnvidia*",
        ],
        "kernel_log_current_boot": [
            "journalctl",
            "-k",
            "-b",
            "--grep",
            "NVRM|nvidia",
            "--no-pager",
        ],
        "boot_time": ["uptime", "-s"],
    }
    record = {
        "evidence_type": "nvidia_driver_library_mismatch_diagnosis",
        "captured_at": utc_now(),
        "profile_id": PROFILE_ID,
        "commands": {name: command(argv) for name, argv in commands.items()},
    }
    write_json(EVIDENCE / "nvidia-mismatch-diagnosis.raw.json", record)


def capture_probe_logs(since: str) -> None:
    record = {
        "captured_at": utc_now(),
        "scope": "Local Ollama service evidence spanning the Phase 1 measured probes",
        "journal": command(
            [
                "journalctl",
                "-u",
                "ollama",
                "--since",
                since,
                "--no-pager",
            ]
        ),
        "nvidia_proc_information": command(
            ["sed", "-n", "1,80p", "/proc/driver/nvidia/gpus/0000:01:00.0/information"]
        ),
    }
    write_json(EVIDENCE / "ollama-probe-service-log.raw.json", record)


def write_checksum_manifest() -> None:
    lines: list[str] = []
    for path in sorted(EVIDENCE.rglob("*")):
        if not path.is_file() or path.name == "SHA256SUMS":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(EVIDENCE)}")
    (EVIDENCE / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def pull_model(model: str) -> None:
    slug = model.replace(":", "-").replace("/", "-")
    record = {
        "evidence_type": "local_candidate_pull",
        "candidate": model,
        "profile_id": PROFILE_ID,
        "started_at": utc_now(),
        "ollama_version_before": api("/api/version"),
        "tags_before": api("/api/tags"),
        "storage_before": {
            "filesystem": command(["df", "-B1", "/usr/share/ollama/.ollama/models"]),
            "model_directory": command(["du", "-sb", "/usr/share/ollama/.ollama/models"]),
        },
    }
    record["pull"] = command(["ollama", "pull", model], timeout=3600)
    record["completed_at"] = utc_now()
    record["ollama_version_after"] = api("/api/version")
    record["tags_after"] = api("/api/tags")
    record["storage_after"] = {
        "filesystem": command(["df", "-B1", "/usr/share/ollama/.ollama/models"]),
        "model_directory": command(["du", "-sb", "/usr/share/ollama/.ollama/models"]),
    }
    write_json(EVIDENCE / "models" / slug / "pull.raw.json", record)
    if record["pull"].get("exit_code") != 0:
        raise SystemExit(f"pull failed for {model}; see preserved pull evidence")


def probe_models(models: list[str]) -> None:
    for model in models:
        slug = model.replace(":", "-").replace("/", "-")
        model_dir = EVIDENCE / "models" / slug
        metadata = model_metadata(model)
        write_json(model_dir / "model-metadata.json", metadata)
        warmup_probe = {
            "id": "discarded-warmup",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["status"],
                "properties": {"status": {"type": "string", "enum": ["ready"]}},
            },
            "prompt": "Return only JSON matching the supplied schema with status set to ready.",
        }
        warmup = run_request(model, warmup_probe, 300)
        write_json(model_dir / "warmup-discarded.raw.json", warmup)
        measured: list[dict[str, Any]] = []
        for index, probe in enumerate(PROBES, start=1):
            result = run_request(model, probe, SCORED_TIMEOUT_SECONDS)
            result["probe_id"] = probe["id"]
            result["repetition_index"] = index
            measured.append(result)
            write_json(model_dir / f"probe-{index}-{probe['id']}.raw.json", result)
        ps_after = command(["ollama", "ps"])
        throughputs = [item["warm_output_tokens_per_second"] for item in measured if item["warm_output_tokens_per_second"] is not None]
        latencies = [item["wall_latency_seconds"] for item in measured if item["error"] is None]
        all_measured_latencies = [item["wall_latency_seconds"] for item in measured]
        headrooms = [item["memory"]["minimum_mem_available_bytes"] for item in measured if item["memory"]["minimum_mem_available_bytes"] is not None]
        error_text = json.dumps([item["error"] for item in measured], sort_keys=True)
        oom_detected = bool(re.search(r"out of memory|\boom\b|cuda.*alloc", error_text, re.IGNORECASE))
        median_throughput = statistics.median(throughputs) if throughputs else None
        median_latency = statistics.median(latencies) if latencies else None
        minimum_headroom = min(headrooms) if headrooms else None
        quantization = (metadata.get("details") or {}).get("quantization_level")
        gates = {
            "q4_k_m_or_documented_equivalent": quantization == "Q4_K_M",
            "no_oom": not oom_detected,
            "at_least_1_gib_system_memory_headroom": minimum_headroom is not None
            and minimum_headroom >= 1024**3,
            "median_warm_output_tokens_per_second_at_least_2": median_throughput is not None
            and median_throughput >= 2,
            "median_successful_wall_latency_seconds_at_most_120": median_latency is not None
            and median_latency <= SCORED_TIMEOUT_SECONDS,
        }
        summary = {
            "evidence_type": "preliminary_hardware_validation_not_benchmark_scores",
            "model": model,
            "hardware_profile_id": PROFILE_ID,
            "ollama_version": api("/api/version")["version"],
            "request_context_tokens": NUM_CTX,
            "thinking_requested": False,
            "structured_output_control": "Ollama /api/chat format=<JSON Schema>",
            "schema_compatibility_note": (
                "Date pattern uses the semantics-preserving ASCII [0-9] class because Ollama "
                "0.32.5 rejected the original JSON Schema \\d escape before model execution."
            ),
            "tag_digest": metadata["tag_record"].get("digest"),
            "on_disk_size_bytes": metadata["tag_record"].get("size"),
            "parameter_size": (metadata.get("details") or {}).get("parameter_size"),
            "quantization": quantization,
            "native_context_fields": metadata.get("native_context_fields"),
            "capabilities": metadata.get("capabilities"),
            "warmup_discarded": True,
            "measured_probe_count": len(measured),
            "successful_probe_count": sum(item["error"] is None for item in measured),
            "strict_json_success_count": sum(item["strict_json_parse_ok"] for item in measured),
            "schema_success_count": sum(item["schema_check_ok"] for item in measured),
            "median_warm_output_tokens_per_second": median_throughput,
            "median_wall_latency_seconds": median_latency,
            "median_successful_wall_latency_seconds": median_latency,
            "median_all_measured_wall_latency_seconds": statistics.median(all_measured_latencies),
            "minimum_observed_system_memory_headroom_bytes": minimum_headroom,
            "oom_detected": oom_detected,
            "ollama_ps_after_measured_probes": ps_after,
            "probe_measurements": [
                {
                    "probe_id": item["probe_id"],
                    "wall_latency_seconds": item["wall_latency_seconds"],
                    "output_tokens": item["output_tokens"],
                    "warm_output_tokens_per_second": item["warm_output_tokens_per_second"],
                    "minimum_mem_available_bytes": item["memory"]["minimum_mem_available_bytes"],
                    "strict_json_parse_ok": item["strict_json_parse_ok"],
                    "schema_check_ok": item["schema_check_ok"],
                    "timed_out": item["timed_out"],
                    "error": item["error"],
                }
                for item in measured
            ],
            "viability_gates": gates,
            "hardware_classification": (
                "Viable on TheImp" if all(gates.values()) else "Impractical on this hardware"
            ),
            "probe_files": [f"probe-{index}-{probe['id']}.raw.json" for index, probe in enumerate(PROBES, start=1)],
        }
        write_json(model_dir / "summary.json", summary)
        write_json(model_dir / "unload-response.json", unload(model))
        time.sleep(2)


def main() -> None:
    global EVIDENCE, PROFILE_ID

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=DEFAULT_EVIDENCE,
        help="evidence destination; pass a new directory when runtime provenance changes",
    )
    parser.add_argument("--profile-id", default=PROFILE_ID)
    parser.add_argument("--hardware", action="store_true")
    parser.add_argument("--runtime-state")
    parser.add_argument("--upgrade-provenance", action="store_true")
    parser.add_argument("--nvidia-diagnosis", action="store_true")
    parser.add_argument("--logs", metavar="SINCE", help="capture Ollama journal entries since this timestamp")
    parser.add_argument("--manifest", action="store_true")
    parser.add_argument("--pull-model")
    parser.add_argument("--models", nargs="*")
    args = parser.parse_args()
    EVIDENCE = args.evidence_dir.resolve()
    PROFILE_ID = args.profile_id
    if socket.gethostname() != "TheImp":
        raise SystemExit(f"refusing substantive capture on hostname {socket.gethostname()!r}; expected 'TheImp'")
    if args.hardware:
        capture_hardware()
    if args.runtime_state:
        capture_runtime_state(args.runtime_state)
    if args.upgrade_provenance:
        capture_upgrade_provenance()
    if args.nvidia_diagnosis:
        capture_nvidia_diagnosis()
    if args.logs:
        capture_probe_logs(args.logs)
    if args.pull_model:
        pull_model(args.pull_model)
    if args.models:
        probe_models(args.models)
    if args.manifest:
        write_checksum_manifest()
    if (
        not args.hardware
        and not args.runtime_state
        and not args.upgrade_provenance
        and not args.nvidia_diagnosis
        and not args.logs
        and not args.manifest
        and not args.pull_model
        and not args.models
    ):
        parser.error(
            "choose --hardware, --runtime-state, --upgrade-provenance, --nvidia-diagnosis, "
            "--logs, --pull-model, --manifest, and/or --models"
        )


if __name__ == "__main__":
    main()
