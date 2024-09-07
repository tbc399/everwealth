CREATE TABLE transaction_refreshes(
    id VARCHAR(22) PRIMARY KEY,
    user_id VARCHAR(22) REFERENCES users(id),
    account_id VARCHAR(22) REFERENCES accounts(id),
    stripe_id VARCHAR(50),
    completed BOOLEAN,
    updated_at TIMESTAMP,
    created_at TIMESTAMP
);

CREATE INDEX transaction_refreshes_id_index ON transaction_refreshes(id);
