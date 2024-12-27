DROP TABLE IF EXISTS firmware_requests;

-- SQL Dump for 'updates' table
CREATE TABLE IF NOT EXISTS updates (
    id SERIAL PRIMARY KEY,          -- Unique identifier for the update
    car_id INTEGER NOT NULL,        -- Foreign key for the car ID
    firmware VARCHAR(50) NOT NULL,   -- Firmware version
    timestamp TIMESTAMP NOT NULL    -- Timestamp of the update
);
