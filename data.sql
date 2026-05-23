CREATE DATABASE IF NOT EXISTS waze_db;
USE waze_db;


-- =====================================================
-- ALERTS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS alerts (

    id VARCHAR(255) PRIMARY KEY,

    type VARCHAR(100),
    subtype VARCHAR(100),

    street TEXT,

    latitude DOUBLE,
    longitude DOUBLE,

    n_comments INT DEFAULT 0,
    n_thumbs_up INT DEFAULT 0,

    comments JSON,

    report_description TEXT,
    report_by VARCHAR(255),

    pub_millis BIGINT,

    -- readable date/time
    pub_datetime DATETIME,

    -- optional computed age
    age_minutes DOUBLE,

    raw_json JSON,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_alert_type (type),
    INDEX idx_alert_street (street(100)),
    INDEX idx_alert_pub (pub_millis),
    INDEX idx_alert_location (latitude, longitude)

);


-- =====================================================
-- JAMS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS jams (

    id BIGINT PRIMARY KEY,

    street TEXT,
    city VARCHAR(255),

    level INT,

    length DOUBLE,
    speed DOUBLE,

    end_node TEXT,

    latitude DOUBLE,
    longitude DOUBLE,

    update_millis BIGINT,

    update_datetime DATETIME,

    -- estimated jam age
    age_minutes DOUBLE,

    -- geometry
    line JSON,

    -- road segments
    segments JSON,

    -- linked alert
    cause_alert JSON,

    -- extracted fields from causeAlert
    cause_type VARCHAR(100),
    cause_subtype VARCHAR(100),
    report_by VARCHAR(255),

    confidence INT,
    reliability INT,

    raw_json JSON,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_jam_level (level),
    INDEX idx_jam_speed (speed),
    INDEX idx_jam_city (city),
    INDEX idx_jam_update (update_millis),
    INDEX idx_jam_location (latitude, longitude)

);