from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from pydantic import ValidationError

from goodenough_bench.boundaries import (
    AcceptanceRules,
    BenchmarkCase,
    BenchmarkRequest,
    CaseStatus,
    CollectionContext,
    Difficulty,
    ErrorType,
    ExecutionEnvironment,
    HumanOverride,
    IdentityConfidence,
    MissingInformationAction,
    MissingInformationPolicy,
    ModelParameters,
    ModelProfileReference,
    NormalizedAdapterResponse,
    ParseBoundaryRecord,
    PlannedRun,
    ProviderSurface,
    RawArtifactReference,
    RedactionStatus,
    ReviewOutcome,
    ReviewRecord,
    ScoreBoundaryRecord,
    SourceType,
    TaskFamily,
)


CHECKSUM = "a" * 64
DATASET_COMMIT = "b" * 40
RUNNER_COMMIT = "c" * 40
STARTED = datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc)


def model_parameters() -> ModelParameters:
    return ModelParameters(
        temperature=0.0,
        max_output_tokens=256,
        reasoning_mode=None,
        response_format="json_schema",
        seed=None,
        top_p=None,
        frequency_penalty=None,
        presence_penalty=None,
    )


def local_profile_data() -> dict[str, object]:
    return {
        "model_profile_id": "qwen35-9b-ollama-q4km",
        "exact_model_identifier": "qwen3.5:9b",
        "displayed_model_name": "Qwen 3.5 9B",
        "provider": "ollama",
        "provider_surface": ProviderSurface.OLLAMA_LOCAL,
        "provider_host": "localhost",
        "source_type": SourceType.LOCAL_EXACT,
        "collection_method": "goodenough-ollama-adapter/0.1.0",
        "model_identity_confidence": IdentityConfidence.HIGH,
        "execution_environment": ExecutionEnvironment.LOCAL,
        "runtime": "ollama 0.32.5",
        "quantization": "Q4_K_M",
        "hardware_profile_id": "theimp-2026-07-31-ollama-0.32.5",
        "pricing_snapshot_id": None,
        "model_parameters": model_parameters(),
    }


def collection_context() -> CollectionContext:
    profile = ModelProfileReference.model_validate(local_profile_data())
    return CollectionContext(
        dataset_version="automation-mvp-v0.1.0",
        dataset_commit=DATASET_COMMIT,
        runner_commit=RUNNER_COMMIT,
        prompt_version="automation-prompt-v0.1.0",
        prompt_hash=CHECKSUM,
        exact_model_identifier=profile.exact_model_identifier,
        displayed_model_name=profile.displayed_model_name,
        provider=profile.provider,
        provider_surface=profile.provider_surface,
        provider_host=profile.provider_host,
        collection_method=profile.collection_method,
        model_identity_confidence=profile.model_identity_confidence,
        source_type=profile.source_type,
        execution_environment=profile.execution_environment,
        runtime=profile.runtime,
        quantization=profile.quantization,
        hardware_profile_id=profile.hardware_profile_id,
        model_parameters=profile.model_parameters,
        pricing_snapshot_id=profile.pricing_snapshot_id,
    )


class BoundaryConstructionTests(unittest.TestCase):
    def test_valid_case_request_profile_plan_and_artifact_construct(self) -> None:
        approved_at = STARTED - timedelta(days=1)
        case = BenchmarkCase(
            case_id="extraction_invoice_001",
            version="0.1.0",
            suite_version="automation-mvp-v0.1.0",
            task_family=TaskFamily.STRUCTURED_EXTRACTION,
            difficulty=Difficulty.MEDIUM,
            status=CaseStatus.APPROVED,
            author="author-1",
            author_review=ReviewRecord(
                reviewer="author-1",
                reviewed_at=approved_at,
                outcome=ReviewOutcome.APPROVED,
                notes="checked",
            ),
            independent_review=ReviewRecord(
                reviewer="reviewer-2",
                reviewed_at=approved_at,
                outcome=ReviewOutcome.APPROVED,
                notes="approved",
            ),
            tags=["invoice", "missing_info"],
            input_text="Invoice number 42; customer name is absent.",
            input_metadata={"source_type": "synthetic", "locale": "en-US"},
            output_schema={
                "type": "object",
                "properties": {"invoice_number": {"type": "string"}},
                "required": ["invoice_number"],
                "additionalProperties": False,
            },
            expected={"invoice_number": "42"},
            acceptance_rules=AcceptanceRules(
                allow_semantic_variants=False,
                critical_fields=["invoice_number"],
                forbidden_inventions=["customer_name"],
                missing_information_policy=MissingInformationPolicy(
                    action=MissingInformationAction.RETURN_NULL,
                    applies_to_fields=["customer_name"],
                ),
                enum_strict=True,
            ),
            notes="A typed boundary fixture, not a corpus case.",
        )
        profile = ModelProfileReference.model_validate(local_profile_data())
        request = BenchmarkRequest(
            run_id="run-001",
            case_id=case.case_id,
            model_profile_id=profile.model_profile_id,
            system_prompt="Return only JSON.",
            user_prompt="Extract the invoice number.",
            output_schema=case.output_schema,
            model_parameters=profile.model_parameters,
            prompt_hash=CHECKSUM,
            timeout_seconds=120,
        )
        planned = PlannedRun(
            **collection_context().model_dump(),
            run_id=request.run_id,
            batch_id="batch-001",
            case_id=case.case_id,
            case_version=case.version,
            model_profile_id=profile.model_profile_id,
            rep_index=0,
            run_order_seed=42,
        )
        artifact = RawArtifactReference(
            raw_id="raw-001",
            run_id=planned.run_id,
            raw_artifact_ref="sha256/aa/raw-001.json",
            raw_checksum=CHECKSUM,
            byte_length=24,
            media_type="application/json",
            redaction_status=RedactionStatus.PRIVATE,
        )

        self.assertEqual(case.task_family, TaskFamily.STRUCTURED_EXTRACTION)
        self.assertEqual(request.timeout_seconds, 120)
        self.assertEqual(planned.rep_index, 0)
        self.assertEqual(artifact.raw_checksum, CHECKSUM)

    def test_response_serialization_retains_explicit_null_provider_fields(self) -> None:
        response = NormalizedAdapterResponse(
            **collection_context().model_dump(),
            run_id="run-001",
            case_id="case-001",
            model_profile_id="qwen35-9b-ollama-q4km",
            run_timestamp=STARTED,
            started_at=STARTED,
            first_token_at=None,
            completed_at=STARTED + timedelta(seconds=2),
            latency_ms=2000,
            input_tokens=None,
            output_tokens=None,
            token_count_inferred=True,
            raw_artifact_ref="sha256/aa/raw-001.json",
            raw_checksum=CHECKSUM,
            error_type=ErrorType.NONE,
            error_message=None,
            retry_count=0,
            estimated_cost=Decimal("0"),
            runtime_metadata={"load_duration_ms": 50},
            hardware_metadata=None,
            provider_request_id=None,
        )

        serialized = response.model_dump(mode="json")
        self.assertIn("first_token_at", serialized)
        self.assertIsNone(serialized["first_token_at"])
        self.assertIn("provider_request_id", serialized)
        self.assertIsNone(serialized["provider_request_id"])
        self.assertNotIn("parsed_json", serialized)
        self.assertNotIn("scorer_version", serialized)

    def test_parse_and_score_records_are_separate_and_valid(self) -> None:
        parsed = ParseBoundaryRecord(
            parsed_id="parsed-001",
            run_id="run-001",
            raw_artifact_ref="sha256/aa/raw-001.json",
            raw_checksum=CHECKSUM,
            parser_version="0.1.0",
            parse_success=True,
            parsed_json={"invoice_number": "42"},
            parse_errors=[],
            schema_valid=True,
            schema_errors=[],
        )
        override = HumanOverride(
            override_id="override-001",
            run_id="run-001",
            reviewer="reviewer-2",
            timestamp=STARTED,
            field_changed="case_pass",
            original_value=False,
            new_value=True,
            reason="Fixture demonstrates explicit override provenance.",
        )
        score = ScoreBoundaryRecord(
            score_id="score-001",
            run_id="run-001",
            parsed_id=parsed.parsed_id,
            task_family=TaskFamily.STRUCTURED_EXTRACTION,
            scorer_version="0.1.0",
            metrics={"normalized_field_accuracy": Decimal("1.0")},
            case_pass=True,
            failure_reasons=[],
            result_checksum=CHECKSUM,
            human_overrides=[override],
        )

        self.assertTrue(parsed.parse_success)
        self.assertEqual(score.scorer_version, "0.1.0")
        self.assertEqual(len(score.human_overrides), 1)


class BoundaryValidationTests(unittest.TestCase):
    def test_required_nullable_provenance_cannot_be_omitted(self) -> None:
        profile_data = local_profile_data()
        del profile_data["pricing_snapshot_id"]

        with self.assertRaises(ValidationError):
            ModelProfileReference.model_validate(profile_data)

        context_data = collection_context().model_dump()
        del context_data["runner_commit"]
        with self.assertRaises(ValidationError):
            CollectionContext.model_validate(context_data)

    def test_local_exact_profile_requires_runtime_hardware_and_quantization(self) -> None:
        for missing_field in ("runtime", "hardware_profile_id", "quantization"):
            with self.subTest(missing_field=missing_field):
                profile_data = local_profile_data()
                profile_data[missing_field] = None
                with self.assertRaisesRegex(ValidationError, "local_exact profiles require"):
                    ModelProfileReference.model_validate(profile_data)

    def test_cloud_profile_requires_explicit_null_local_fields(self) -> None:
        cloud_data = local_profile_data()
        cloud_data.update(
            {
                "model_profile_id": "gpt-luna-openai",
                "exact_model_identifier": "gpt-5.6-luna",
                "provider": "openai",
                "provider_surface": ProviderSurface.OPENAI_RESPONSES_API,
                "provider_host": "api.openai.com",
                "source_type": SourceType.API_EXACT,
                "execution_environment": ExecutionEnvironment.CLOUD,
                "runtime": "openai-python 1.x",
                "quantization": None,
                "hardware_profile_id": None,
            }
        )
        profile = ModelProfileReference.model_validate(cloud_data)
        self.assertIsNone(profile.quantization)
        self.assertIsNone(profile.hardware_profile_id)

        cloud_data["hardware_profile_id"] = "theimp"
        with self.assertRaisesRegex(ValidationError, "represent hardware"):
            ModelProfileReference.model_validate(cloud_data)

    def test_adapter_cannot_emit_parse_failure(self) -> None:
        with self.assertRaisesRegex(ValidationError, "ParseBoundaryRecord"):
            NormalizedAdapterResponse(
                **collection_context().model_dump(),
                run_id="run-001",
                case_id="case-001",
                model_profile_id="qwen35-9b-ollama-q4km",
                run_timestamp=STARTED,
                started_at=STARTED,
                first_token_at=None,
                completed_at=STARTED + timedelta(seconds=1),
                latency_ms=1000,
                input_tokens=None,
                output_tokens=None,
                token_count_inferred=True,
                raw_artifact_ref="sha256/aa/raw-001.json",
                raw_checksum=CHECKSUM,
                error_type=ErrorType.PARSE_FAILURE,
                error_message="adapter attempted to parse",
                retry_count=0,
                estimated_cost=None,
                runtime_metadata=None,
                hardware_metadata=None,
                provider_request_id=None,
            )

    def test_failed_parse_cannot_contain_repaired_json(self) -> None:
        with self.assertRaisesRegex(ValidationError, "no parsed_json"):
            ParseBoundaryRecord(
                parsed_id="parsed-001",
                run_id="run-001",
                raw_artifact_ref="sha256/aa/raw-001.json",
                raw_checksum=CHECKSUM,
                parser_version="0.1.0",
                parse_success=False,
                parsed_json={"repaired": True},
                parse_errors=["invalid JSON"],
                schema_valid=None,
                schema_errors=[],
            )


if __name__ == "__main__":
    unittest.main()
