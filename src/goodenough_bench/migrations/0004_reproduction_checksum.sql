-- Persist provenance fingerprint set when a batch becomes frozen.
ALTER TABLE benchmark_batches
    ADD COLUMN reproduction_checksum TEXT NULL;

-- Earlier schema versions permitted frozen batches without this fingerprint.
-- Reclassify those legacy records as completed so a verified freeze can be
-- created explicitly through the lifecycle boundary.
UPDATE benchmark_batches
SET status = 'completed'
WHERE status = 'frozen';
