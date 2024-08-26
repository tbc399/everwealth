CREATE TYPE AssetType AS ENUM ('vehicle', 'property', 'other');

CREATE TABLE assets(
    id VARCHAR(22) PRIMARY KEY,
    name VARCHAR(50),
    type AssetType,
    user_id VARCHAR(22) REFERENCES users(id),
    last_sync TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX assets_id_index ON assets(id);
