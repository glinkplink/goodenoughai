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
EVIDENCE = ROOT / "evidence" / "phase1-theimp-2026-07-31"
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
                "date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
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


def command(argv: list[str]) -> dict[str, Any]:
    started = utc_now()
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30, check=False)
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
        "profile_id": "theimp-2026-07-31",
        "captured_at": utc_now(),
        "hostname_python": socket.gethostname(),
        "platform_python": platform.platform(),
        "working_directory": str(ROOT),
        "commands": {name: command(argv) for name, argv in commands.items()},
        "ollama_api_version": api("/api/version"),
        "ollama_api_tags": api("/api/tags"),
    }
    write_json(EVIDENCE / "hardware-runtime-profile.raw.json", record)


def capture_probe_logs() -> None:
    record = {
        "captured_at": utc_now(),
        "scope": "Local Ollama service evidence spanning the Phase 1 measured probes",
        "journal": command(
            [
                "journalctl",
                "-u",
                "ollama",
                "--since",
                "2026-07-31 22:26:30",
                "--until",
                "2026-07-31 22:27:00",
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
        headrooms = [item["memory"]["minimum_mem_available_bytes"] for item in measured if item["memory"]["minimum_mem_available_bytes"] is not None]
        summary = {
            "evidence_type": "preliminary_hardware_validation_not_benchmark_scores",
            "model": model,
            "hardware_profile_id": "theimp-2026-07-31",
            "ollama_version": api("/api/version")["version"],
            "request_context_tokens": NUM_CTX,
            "thinking_requested": False,
            "structured_output_control": "Ollama /api/chat format=<JSON Schema>",
            "warmup_discarded": True,
            "measured_probe_count": len(measured),
            "successful_probe_count": sum(item["error"] is None for item in measured),
            "strict_json_success_count": sum(item["strict_json_parse_ok"] for item in measured),
            "schema_success_count": sum(item["schema_check_ok"] for item in measured),
            "median_warm_output_tokens_per_second": statistics.median(throughputs) if throughputs else None,
            "median_wall_latency_seconds": statistics.median(latencies) if latencies else None,
            "minimum_observed_system_memory_headroom_bytes": min(headrooms) if headrooms else None,
            "ollama_ps_after_measured_probes": ps_after,
            "probe_files": [f"probe-{index}-{probe['id']}.raw.json" for index, probe in enumerate(PROBES, start=1)],
        }
        write_json(model_dir / "summary.json", summary)
        write_json(model_dir / "unload-response.json", unload(model))
        time.sleep(2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hardware", action="store_true")
    parser.add_argument("--logs", action="store_true")
    parser.add_argument("--manifest", action="store_true")
    parser.add_argument("--models", nargs="*")
    args = parser.parse_args()
    if socket.gethostname() != "TheImp":
        raise SystemExit(f"refusing substantive capture on hostname {socket.gethostname()!r}; expected 'TheImp'")
    if args.hardware:
        capture_hardware()
    if args.logs:
        capture_probe_logs()
    if args.models:
        probe_models(args.models)
    if args.manifest:
        write_checksum_manifest()
    if not args.hardware and not args.logs and not args.manifest and not args.models:
        parser.error("choose --hardware, --logs, --manifest, and/or --models")


if __name__ == "__main__":
    main()
