CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    checksum TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE benchmark_batches (
    batch_id TEXT PRIMARY KEY,
    dataset_version TEXT NOT NULL,
    dataset_commit TEXT NOT NULL,
    runner_commit TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    run_order_seed INTEGER NOT NULL,
    operator TEXT NOT NULL,
    environment TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('planned', 'running', 'completed', 'frozen')),
    started_at TEXT NULL,
    completed_at TEXT NULL,
    invalid_run_count INTEGER NOT NULL CHECK (invalid_run_count >= 0),
    valid_for_scoring_count INTEGER NOT NULL CHECK (valid_for_scoring_count >= 0)
);

CREATE TABLE planned_runs (
    run_id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL REFERENCES benchmark_batches(batch_id),
    case_id TEXT NOT NULL,
    case_version TEXT NOT NULL,
    model_profile_id TEXT NOT NULL,
    rep_index INTEGER NOT NULL CHECK (rep_index >= 0),
    run_order_seed INTEGER NOT NULL,
    dataset_version TEXT NOT NULL,
    dataset_commit TEXT NOT NULL,
    runner_commit TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    exact_model_identifier TEXT NOT NULL,
    displayed_model_name TEXT NOT NULL,
    provider TEXT NOT NULL,
    provider_surface TEXT NOT NULL,
    provider_host TEXT NULL,
    collection_method TEXT NOT NULL,
    model_identity_confidence TEXT NOT NULL,
    source_type TEXT NOT NULL,
    execution_environment TEXT NOT NULL,
    runtime TEXT NULL,
    quantization TEXT NULL,
    hardware_profile_id TEXT NULL,
    pricing_snapshot_id TEXT NULL,
    model_parameters_json TEXT NOT NULL,
    UNIQUE (batch_id, model_profile_id, case_id, rep_index)
);
