ALTER TABLE planned_runs
    ADD COLUMN local_model_identity_json TEXT NULL;

ALTER TABLE planned_runs
    ADD COLUMN routed_provider_identity_json TEXT NULL;

ALTER TABLE planned_runs
    ADD COLUMN profile_provenance_complete INTEGER NOT NULL
    DEFAULT 0
    CHECK (profile_provenance_complete IN (0, 1));
