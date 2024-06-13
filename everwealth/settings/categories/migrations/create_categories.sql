CREATE TABLE categories (
    id VARCHAR(22) PRIMARY KEY,
    name VARCHAR(64),
    user_id VARCHAR(22) REFERENCES users(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX categories_id_index on categories(id);

