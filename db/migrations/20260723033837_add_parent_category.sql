-- migrate:up
ALTER TABLE categories ADD COLUMN IF NOT EXISTS parent_id VARCHAR(22) REFERENCES categories(id);


-- migrate:down
ALTER TABLE categories DROP COLUMN IF EXISTS parent_id;
