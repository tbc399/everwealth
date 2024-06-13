CREATE TABLE otp (
    id VARCHAR(22) PRIMARY KEY,
    magic_token VARCHAR(64),
    code INTEGER, 
    email VARCHAR(64),
    expiry TIMESTAMP,
    invalidated BOOLEAN,
    created_at TIMESTAMP
);

CREATE INDEX otp_id_index ON otp(id);
CREATE INDEX otp_magic_token_index ON otp(magic_token);
