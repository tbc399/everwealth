CREATE TABLE accounts(
    id VARCHAR(22) PRIMARY KEY,
    user_id VARCHAR(22) REFERENCES users(id),
    created_at TIMESTAMP
);

CREATE INDEX accounts_id_index ON accounts(id);
