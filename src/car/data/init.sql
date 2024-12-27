DROP TABLE IF EXISTS updates;

-- SQL Dump for 'updates' table
CREATE TABLE IF NOT EXISTS updates (
    id SERIAL PRIMARY KEY,          -- Unique identifier for the update
    car_id INTEGER NOT NULL,        -- Foreign key for the car ID
    user_id VARCHAR(50) NOT NULL,   -- User ID who made the update
    config JSON NOT NULL,           -- Configuration details in JSON format
    firmware VARCHAR(10) NOT NULL   -- Firmware version
);
