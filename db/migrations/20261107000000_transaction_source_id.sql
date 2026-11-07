-- migrate:up
-- Development reset: old process-dependent hashes cannot identify imported rows reliably.
DELETE FROM transactions;
ALTER TABLE transactions DROP COLUMN source_hash;
ALTER TABLE transactions ADD COLUMN source_id TEXT NOT NULL UNIQUE;

-- migrate:down
DELETE FROM transactions;
ALTER TABLE transactions DROP COLUMN source_id;
ALTER TABLE transactions ADD COLUMN source_hash BIGINT;
