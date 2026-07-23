-- migrate:up
CREATE TYPE Frequency AS ENUM ('monthly', 'yearly');

CREATE TABLE budgets (
    id VARCHAR(22) PRIMARY KEY,
    user_id VARCHAR(22) REFERENCES users(id),
    category_id VARCHAR(22) REFERENCES categories(id),
    amount INTEGER,
    rollover BOOLEAN,
    frequency Frequency,
    year INTEGER,
    month INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX budgets_id_index ON budgets(id);
CREATE INDEX budgets_user_id_index ON budgets(user_id);

-- migrate:down
DROP INDEX IF EXISTS budgets_user_id_index;
DROP INDEX IF EXISTS budgets_id_index;
DROP TABLE IF EXISTS budgets;
DROP TYPE IF EXISTS Frequency;
