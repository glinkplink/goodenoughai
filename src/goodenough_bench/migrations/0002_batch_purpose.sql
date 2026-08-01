ALTER TABLE benchmark_batches
    ADD COLUMN batch_purpose TEXT NOT NULL
    DEFAULT 'diagnostic_pilot'
    CHECK (batch_purpose IN ('diagnostic_pilot', 'stable_benchmark'));
