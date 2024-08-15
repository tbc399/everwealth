CREATE TYPE AccountType AS ENUM ('cash', 'credit', 'investment', 'other', 'manual');

CREATE TABLE accounts(
    id VARCHAR(22) PRIMARY KEY,
    name VARCHAR(50),
    type AccountType,
    user_id VARCHAR(22) REFERENCES users(id),
    institution_name: VARCHAR(50),
    stripe_id: VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX accounts_id_index ON accounts(id);
