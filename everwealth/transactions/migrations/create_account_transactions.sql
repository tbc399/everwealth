CREATE TABLE transactions(
    id VARCHAR(22) PRIMARY KEY,
    source_hash INTEGER,
    user_id VARCHAR(22) REFERENCES users(id),
    account_id VARCHAR(22) REFERENCES accounts(id),
    description VARCHAR(128),
    amount FLOAT NOT NULL, 
    category_id VARCHAR(22) REFERENCES transactions(id), 
    date DATE,
    notes VARCHAR(256),
    hidden BOOLEAN
);

CREATE INDEX transactions_id_index ON transactions(id);
