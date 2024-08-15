CREATE TABLE users(
    id VARCHAR(22) PRIMARY KEY,
    first VARCHAR(64),
    last VARCHAR(64),
    email VARCHAR(64),
    stripe_customer_id VARCHAR(18),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX users_id_index ON users(id);
CREATE INDEX users_email_index ON users(email);
