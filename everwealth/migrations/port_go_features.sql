BEGIN;

CREATE TABLE IF NOT EXISTS budget_periods (
    id VARCHAR(22) PRIMARY KEY,
    user_id VARCHAR(22) REFERENCES users(id),
    start TIMESTAMP NOT NULL,
    "end" TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS budget_periods_user_id_index ON budget_periods(user_id);

ALTER TABLE budgets ADD COLUMN IF NOT EXISTS period_id VARCHAR(22) REFERENCES budget_periods(id);
ALTER TABLE budgets ADD COLUMN IF NOT EXISTS rollover BOOLEAN DEFAULT FALSE;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'budgets' AND column_name = 'year'
    ) THEN
        INSERT INTO budget_periods (id, user_id, start, "end", created_at)
        SELECT substr(md5(user_id || year::text || month::text), 1, 22),
               user_id,
               make_date(year, month, 1)::timestamp,
               (make_date(year, month, 1) + interval '1 month - 1 second')::timestamp,
               NOW()
        FROM budgets
        WHERE period_id IS NULL
        GROUP BY user_id, year, month
        ON CONFLICT (id) DO NOTHING;

        UPDATE budgets
        SET period_id = substr(md5(user_id || year::text || month::text), 1, 22)
        WHERE period_id IS NULL;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS plaid_items (
    id VARCHAR(22) PRIMARY KEY,
    user_id VARCHAR(22) REFERENCES users(id),
    access_token TEXT NOT NULL,
    institution_id VARCHAR(128),
    item_id VARCHAR(128) UNIQUE NOT NULL,
    transactions_cursor TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
ALTER TABLE plaid_items ADD COLUMN IF NOT EXISTS transactions_cursor TEXT;

ALTER TABLE accounts ADD COLUMN IF NOT EXISTS plaid_item_id VARCHAR(22) REFERENCES plaid_items(id);
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS plaid_account_id VARCHAR(128);
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS last_sync TIMESTAMP;
CREATE UNIQUE INDEX IF NOT EXISTS accounts_plaid_account_id_unique
    ON accounts(plaid_item_id, plaid_account_id)
    WHERE plaid_account_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS assets (
    id VARCHAR(22) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL,
    user_id VARCHAR(22) REFERENCES users(id),
    last_sync TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS assets_user_id_index ON assets(user_id);

ALTER TABLE transactions ADD COLUMN IF NOT EXISTS orig_description VARCHAR(128);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS orig_amount INTEGER;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS orig_date DATE;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS plaid_transaction_id VARCHAR(128);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
CREATE UNIQUE INDEX IF NOT EXISTS transactions_plaid_transaction_id_unique
    ON transactions(plaid_transaction_id)
    WHERE plaid_transaction_id IS NOT NULL;

UPDATE transactions SET orig_description = description WHERE orig_description IS NULL;
UPDATE transactions SET orig_amount = ROUND(amount * 100)::INTEGER WHERE orig_amount IS NULL;
UPDATE transactions SET orig_date = date WHERE orig_date IS NULL;
UPDATE transactions SET created_at = NOW() WHERE created_at IS NULL;
UPDATE transactions SET updated_at = NOW() WHERE updated_at IS NULL;
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'transactions'
          AND column_name = 'amount'
          AND data_type <> 'integer'
    ) THEN
        ALTER TABLE transactions
        ALTER COLUMN amount TYPE INTEGER USING ROUND(amount * 100)::INTEGER;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS profiles (
    id VARCHAR(22) PRIMARY KEY,
    user_id VARCHAR(22) UNIQUE REFERENCES users(id),
    first VARCHAR(64),
    last VARCHAR(64),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

COMMIT;
