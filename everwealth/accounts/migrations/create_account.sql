CREATE TYPE AccountType AS ENUM ('cash', 'credit', 'investment', 'other', 'manual');
CREATE TYPE AccountSubType AS ENUM ('checking', 'savings', 'credit_card', 'line_of_credit', 'mortgage', 'other');

CREATE TABLE accounts(
    id VARCHAR(22) PRIMARY KEY,
    name VARCHAR(50),
    type AccountType,
    sub_type AccountSubType,
    user_id VARCHAR(22) REFERENCES users(id),
    institution_name VARCHAR(50),
    last4 VARCHAR(4),
    stripe_id: VARCHAR(50),
    last_sync: TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX accounts_id_index ON accounts(id);
