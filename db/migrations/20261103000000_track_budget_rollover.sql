-- migrate:up
-- Existing periods remain pending so empty/partial months can be repaired once.
ALTER TABLE budget_periods
    ADD COLUMN rollover_completed BOOLEAN NOT NULL DEFAULT FALSE;

-- migrate:down
ALTER TABLE budget_periods DROP COLUMN rollover_completed;
