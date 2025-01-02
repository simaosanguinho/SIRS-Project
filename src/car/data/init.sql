DROP TABLE IF EXISTS configurations;
DROP TABLE IF EXISTS firmwares;
DROP TABLE IF EXISTS mechanic_tests;

-- SQL Dump for 'configurations' table
CREATE TABLE IF NOT EXISTS configurations (
    id SERIAL PRIMARY KEY,          -- Unique identifier for the update
    car_id INTEGER NOT NULL,        -- Foreign key for the car ID
    user_id VARCHAR(50) NOT NULL,   -- User ID who made the update
    config JSON NOT NULL            -- Configuration details in JSON format
);

-- SQL Dump for 'firmwares' table
CREATE TABLE IF NOT EXISTS firmwares (
    id SERIAL PRIMARY KEY,          -- Unique identifier for the update
    car_id INTEGER NOT NULL,        -- Foreign key for the car ID
    firmware VARCHAR(50) NOT NULL,   -- Firmware version
    signature TEXT NOT NULL,        -- signature of the firmware
    timestamp TIMESTAMP NOT NULL    -- Timestamp of the update
);


-- SQL Dump for 'mechanic_tests' table
CREATE TABLE IF NOT EXISTS mechanic_tests (
    id SERIAL PRIMARY KEY,          -- Unique identifier for the update
    car_id INTEGER NOT NULL,        -- Foreign key for the car ID
    tests JSON NOT NULL,             -- Test details in JSON format
    signature TEXT NOT NULL,        -- signature of the test
    timestamp TIMESTAMP NOT NULL,   -- Timestamp of the update
    mechanic_cert TEXT NOT NULL     -- Mechanic certificate
);
