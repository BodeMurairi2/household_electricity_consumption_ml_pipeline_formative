CREATE DATABASE IF NOT EXISTS household_power;
USE household_power;

CREATE TABLE households (
    household_id  INT PRIMARY KEY AUTO_INCREMENT,
    name          VARCHAR(100) NOT NULL,
    city          VARCHAR(100) NOT NULL,
    country       VARCHAR(100) NOT NULL,
    data_start    DATETIME,
    data_end      DATETIME
);

CREATE TABLE sub_meters (
    sub_meter_id  INT PRIMARY KEY,
    household_id  INT NOT NULL,
    name          VARCHAR(50) NOT NULL,
    appliances    VARCHAR(255),
    FOREIGN KEY (household_id) REFERENCES households(household_id)
);

CREATE TABLE power_readings (
    reading_id             INT PRIMARY KEY,
    household_id           INT NOT NULL,
    measured_at            DATETIME NOT NULL,
    global_active_power    DECIMAL(6,3),
    global_reactive_power  DECIMAL(6,3),
    voltage                DECIMAL(6,3),
    global_intensity       DECIMAL(6,3),
    UNIQUE KEY uq_household_time (household_id, measured_at),
    FOREIGN KEY (household_id) REFERENCES households(household_id)
);

CREATE TABLE sub_meter_readings (
    reading_id    INT NOT NULL,
    sub_meter_id  INT NOT NULL,
    energy_wh     DECIMAL(6,1) NOT NULL,
    PRIMARY KEY (reading_id, sub_meter_id),
    FOREIGN KEY (reading_id) REFERENCES power_readings(reading_id),
    FOREIGN KEY (sub_meter_id) REFERENCES sub_meters(sub_meter_id)
);

CREATE TABLE hourly_power (
    household_id           INT NOT NULL,
    hour_start             DATETIME NOT NULL,
    global_active_power    DOUBLE,
    global_reactive_power  DOUBLE,
    voltage                DOUBLE,
    global_intensity       DOUBLE,
    sub_metering_1         DOUBLE,
    sub_metering_2         DOUBLE,
    sub_metering_3         DOUBLE,
    PRIMARY KEY (household_id, hour_start),
    FOREIGN KEY (household_id) REFERENCES households(household_id)
);
