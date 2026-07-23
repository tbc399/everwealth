-- migrate:up
CREATE TYPE CategoryType AS ENUM ('income', 'expense');

CREATE TABLE categories (
    id VARCHAR(22) PRIMARY KEY,
    name VARCHAR(64),
    type CategoryType,
    user_id VARCHAR(22) REFERENCES users(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX categories_id_index ON categories(id);
CREATE INDEX categories_user_id_index ON categories(user_id);

-- migrate:down
DROP INDEX IF EXISTS categories_user_id_index;
DROP INDEX IF EXISTS categories_id_index;
DROP TABLE IF EXISTS categories;
DROP TYPE IF EXISTS CategoryType;
