DROP TABLE IF EXISTS firmware_requests;

-- SQL Dump for 'updates' table
CREATE TABLE IF NOT EXISTS firmware_requests (
    id SERIAL PRIMARY KEY,          -- Unique identifier for the update
    car_id INTEGER NOT NULL,        -- Foreign key for the car ID
    firmware VARCHAR(50) NOT NULL,   -- Firmware version
    signature TEXT NOT NULL,        -- signature of the firmware
    timestamp TIMESTAMP NOT NULL    -- Timestamp of the update
);

ALTER TABLE firmware_requests OWNER TO "manufacturer-web";
