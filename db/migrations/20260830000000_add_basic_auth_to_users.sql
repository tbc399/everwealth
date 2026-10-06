-- migrate:up
ALTER TABLE users
ADD COLUMN username VARCHAR(64),
ADD COLUMN password_hash TEXT;

CREATE UNIQUE INDEX users_username_unique_index ON users (lower(username)) WHERE username IS NOT NULL;
CREATE UNIQUE INDEX users_email_unique_index ON users (lower(email)) WHERE email IS NOT NULL;

-- migrate:down
DROP INDEX IF EXISTS users_email_unique_index;
DROP INDEX IF EXISTS users_username_unique_index;

ALTER TABLE users
DROP COLUMN IF EXISTS password_hash,
DROP COLUMN IF EXISTS username;
