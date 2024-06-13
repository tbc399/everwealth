CREATE TABLE sessions(
    id VARCHAR(64) PRIMARY KEY,
    expiry TIMESTAMP,
    otp_id VARCHAR(22) REFERENCES otp(id), 
    user_id VARCHAR(22) REFERENCES users(id),
    device_id VARCHAR(22),
    device_trusted BOOLEAN,
    invalidated BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX sessions_id_index ON sessions(id);
CREATE INDEX sessions_user_id_index ON sessions(user_id);
