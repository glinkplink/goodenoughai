#!/usr/bin/env python3
"""Validate the frozen Ollama 0.32.5 Phase 1 evidence invariants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPECTED_MODELS = {
    "qwen3.5:9b": "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7",
    "gemma4:12b": "4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c",
    "llama3.1:8b": "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e",
}
PROBES = ["extraction", "classification", "normalization"]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def checksum_map(record: dict[str, Any]) -> dict[str, str]:
    stdout = record["commands"]["ollama_binary_and_service_checksums"]["stdout"]
    values: dict[str, str] = {}
    for line in stdout.splitlines():
        digest, path = line.split(maxsplit=1)
        values[path] = digest
    return values


def validate(evidence: Path) -> list[str]:
    errors: list[str] = []
    pre = load(evidence / "runtime-pre-upgrade.raw.json")
    post = load(evidence / "runtime-post-upgrade.raw.json")
    final = load(evidence / "runtime-final-profile.raw.json")
    require(pre["ollama_api_version"]["version"] == "0.17.4", "pre-upgrade daemon is not 0.17.4", errors)
    require(post["ollama_api_version"]["version"] == "0.32.5", "post-upgrade daemon is not 0.32.5", errors)
    require(final["ollama_api_version"]["version"] == "0.32.5", "final daemon is not 0.32.5", errors)
    require(final["ollama_api_ps"]["models"] == [], "a candidate remained loaded in final state", errors)

    pre_checksums = checksum_map(pre)
    final_checksums = checksum_map(final)
    for path in (
        "/etc/systemd/system/ollama.service",
        "/etc/systemd/system/ollama.service.d/override.conf",
    ):
        require(pre_checksums.get(path) == final_checksums.get(path), f"service configuration changed: {path}", errors)

    pre_tags = {item["name"]: item for item in pre["ollama_api_tags"]["models"]}
    final_tags = {item["name"]: item for item in final["ollama_api_tags"]["models"]}
    for name, item in pre_tags.items():
        require(name in final_tags, f"pre-existing model disappeared: {name}", errors)
        if name in final_tags:
            require(item["digest"] == final_tags[name]["digest"], f"digest changed for {name}", errors)
            require(item["size"] == final_tags[name]["size"], f"disk size changed for {name}", errors)
    require(len(pre_tags) == 13, "unexpected pre-upgrade inventory count", errors)
    require(len(final_tags) == 14, "unexpected final inventory count", errors)
    for name, digest in EXPECTED_MODELS.items():
        require(final_tags.get(name, {}).get("digest") == digest, f"wrong final digest for {name}", errors)

    pull = load(evidence / "models" / "gemma4-12b" / "pull.raw.json")
    require(pull["pull"].get("exit_code") == 0, "Gemma pull did not succeed", errors)
    require(pull["ollama_version_before"]["version"] == "0.32.5", "Gemma pull used wrong initial runtime", errors)
    require(pull["ollama_version_after"]["version"] == "0.32.5", "Gemma pull changed runtime", errors)

    original_root = evidence / "models"
    compatible_root = evidence / "compatible-pattern-schema" / "models"
    for model, digest in EXPECTED_MODELS.items():
        slug = model.replace(":", "-")
        original_summary = load(original_root / slug / "summary.json")
        require(original_summary["successful_probe_count"] == 2, f"original incompatibility pass changed for {model}", errors)
        original_normalization = load(original_root / slug / "probe-3-normalization.raw.json")
        original_error = original_normalization.get("error") or {}
        require(original_error.get("status") == 400, f"original normalization did not retain HTTP 400 for {model}", errors)
        require(
            "failed to parse grammar" in original_error.get("response_body", "").lower(),
            f"original grammar failure missing for {model}",
            errors,
        )
        require(
            original_normalization["request"]["format"]["properties"]["date"]["pattern"]
            == r"^\d{4}-\d{2}-\d{2}$",
            f"original date pattern changed for {model}",
            errors,
        )

        model_dir = compatible_root / slug
        summary = load(model_dir / "summary.json")
        require(summary["model"] == model, f"wrong model in summary for {model}", errors)
        require(summary["tag_digest"] == digest, f"wrong summary digest for {model}", errors)
        require(summary["ollama_version"] == "0.32.5", f"wrong probe runtime for {model}", errors)
        require(summary["quantization"] == "Q4_K_M", f"wrong quantization for {model}", errors)
        require(summary["request_context_tokens"] == 4096, f"wrong requested context for {model}", errors)
        require(summary["warmup_discarded"] is True, f"warmup not marked discarded for {model}", errors)
        require(summary["measured_probe_count"] == 3, f"wrong measured count for {model}", errors)
        require(summary["successful_probe_count"] == 3, f"not all probes succeeded for {model}", errors)
        require(summary["strict_json_success_count"] == 3, f"not all JSON parsed for {model}", errors)
        require(summary["schema_success_count"] == 3, f"not all schemas matched for {model}", errors)
        require(summary["oom_detected"] is False, f"OOM detected for {model}", errors)
        require(summary["hardware_classification"] == "Viable on TheImp", f"wrong classification for {model}", errors)
        require(all(summary["viability_gates"].values()), f"a viability gate failed for {model}", errors)

        warmup = load(model_dir / "warmup-discarded.raw.json")
        require(warmup["request"]["model"] == model, f"warmup used wrong model for {model}", errors)
        for index, probe_id in enumerate(PROBES, start=1):
            record = load(model_dir / f"probe-{index}-{probe_id}.raw.json")
            request = record["request"]
            require(record["probe_id"] == probe_id, f"wrong probe id for {model}/{probe_id}", errors)
            require(record["repetition_index"] == index, f"wrong repetition index for {model}/{probe_id}", errors)
            require(request["model"] == model, f"wrong request model for {model}/{probe_id}", errors)
            require(request["stream"] is False, f"stream enabled for {model}/{probe_id}", errors)
            require(request["think"] is False, f"thinking not disabled for {model}/{probe_id}", errors)
            require(request["options"]["temperature"] == 0, f"nonzero temperature for {model}/{probe_id}", errors)
            require(request["options"]["num_ctx"] == 4096, f"wrong context for {model}/{probe_id}", errors)
            require(len(request["messages"]) == 1, f"request history present for {model}/{probe_id}", errors)
            require("tools" not in request, f"tools present for {model}/{probe_id}", errors)
            require(record["error"] is None, f"probe error for {model}/{probe_id}", errors)
            require(record["strict_json_parse_ok"] is True, f"JSON parse failed for {model}/{probe_id}", errors)
            require(record["schema_check_ok"] is True, f"schema check failed for {model}/{probe_id}", errors)
            require(record["timed_out"] is False, f"probe timed out for {model}/{probe_id}", errors)
            if probe_id == "normalization":
                require(
                    request["format"]["properties"]["date"]["pattern"]
                    == "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
                    f"wrong compatible date pattern for {model}",
                    errors,
                )
        unload = load(model_dir / "unload-response.json")
        require(unload.get("error") is None, f"unload failed for {model}", errors)

    nvidia = load(evidence / "nvidia-mismatch-diagnosis.raw.json")
    commands = nvidia["commands"]
    require(commands["loaded_module_sysfs_version"]["stdout"].strip() == "595.71.05", "unexpected loaded NVIDIA module", errors)
    require(commands["installed_module_version"]["stdout"].strip() == "595.84", "unexpected installed NVIDIA module", errors)
    require("595.84" in commands["userspace_nvml_target"]["stdout"], "unexpected NVML userspace target", errors)
    require(commands["nvidia_smi"]["exit_code"] != 0, "nvidia-smi mismatch unexpectedly absent", errors)
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    errors = validate(args.evidence.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("Phase 1 structured-evidence invariants: PASS")


if __name__ == "__main__":
    main()
