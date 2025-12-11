--- Schema for telecom.db ---

Table: customers
------------------------------
CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    address VARCHAR(200),
    service_plan_id VARCHAR(50),
    account_status VARCHAR(20) NOT NULL,
    registration_date DATE NOT NULL,
    last_billing_date DATE,
    FOREIGN KEY (service_plan_id) REFERENCES service_plans(plan_id)
)


Table: service_plans
------------------------------
CREATE TABLE service_plans (
    plan_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    monthly_cost DECIMAL(10,2) NOT NULL,
    data_limit_gb INT,
    unlimited_data BOOLEAN NOT NULL,
    voice_minutes INT,
    unlimited_voice BOOLEAN NOT NULL,
    sms_count INT,
    unlimited_sms BOOLEAN NOT NULL,
    contract_duration_months INT,
    early_termination_fee DECIMAL(10,2),
    international_roaming BOOLEAN NOT NULL,
    description TEXT
)


Table: network_incidents
------------------------------
CREATE TABLE network_incidents (
    incident_id VARCHAR(50) PRIMARY KEY,
    incident_type VARCHAR(50) NOT NULL,
    location VARCHAR(100),
    affected_services TEXT,
    start_time TIMESTAMP NOT NULL,
    resolution_time TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT,
    resolution_details TEXT
)


Table: support_tickets
------------------------------
CREATE TABLE support_tickets (
    ticket_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    issue_category VARCHAR(50) NOT NULL,
    issue_description TEXT NOT NULL,
    creation_time TIMESTAMP NOT NULL,
    resolution_time TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    resolution_notes TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
)


Table: customer_usage
------------------------------
CREATE TABLE customer_usage (
    usage_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,
    data_used_gb DECIMAL(10,2),
    voice_minutes_used INT,
    sms_count_used INT,
    additional_charges DECIMAL(10,2),
    total_bill_amount DECIMAL(10,2),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
)


Table: service_areas
------------------------------
CREATE TABLE service_areas (
    area_id VARCHAR(50) PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20),
    region VARCHAR(100),
    population_density VARCHAR(20), -- High, Medium, Low
    terrain_type VARCHAR(50) -- Urban, Suburban, Rural, etc.
)


Table: cell_towers
------------------------------
CREATE TABLE cell_towers (
    tower_id VARCHAR(50) PRIMARY KEY,
    area_id VARCHAR(50) NOT NULL,
    latitude DECIMAL(10,6) NOT NULL,
    longitude DECIMAL(10,6) NOT NULL,
    tower_type VARCHAR(50) NOT NULL, -- Macro, Micro, Small Cell
    height_meters INT,
    installation_date DATE,
    last_maintenance_date DATE,
    operational_status VARCHAR(20) NOT NULL, -- Active, Maintenance, Offline
    FOREIGN KEY (area_id) REFERENCES service_areas(area_id)
)


Table: tower_technologies
------------------------------
CREATE TABLE tower_technologies (
    tower_tech_id VARCHAR(50) PRIMARY KEY,
    tower_id VARCHAR(50) NOT NULL,
    technology VARCHAR(20) NOT NULL, -- 2G, 3G, 4G, 5G
    frequency_band VARCHAR(20),
    bandwidth_mhz DECIMAL(5,2),
    max_capacity_mbps INT,
    active BOOLEAN NOT NULL,
    FOREIGN KEY (tower_id) REFERENCES cell_towers(tower_id)
)


Table: coverage_quality
------------------------------
CREATE TABLE coverage_quality (
    coverage_id VARCHAR(50) PRIMARY KEY,
    area_id VARCHAR(50) NOT NULL,
    technology VARCHAR(20) NOT NULL, -- 4G, 5G, etc.
    signal_strength_category VARCHAR(20) NOT NULL, -- Excellent, Good, Fair, Poor
    avg_download_speed_mbps DECIMAL(10,2),
    avg_upload_speed_mbps DECIMAL(10,2),
    avg_latency_ms INT,
    last_updated TIMESTAMP NOT NULL,
    FOREIGN KEY (area_id) REFERENCES service_areas(area_id)
)


Table: transportation_routes
------------------------------
CREATE TABLE transportation_routes (
    route_id VARCHAR(50) PRIMARY KEY,
    route_name VARCHAR(100) NOT NULL,
    route_type VARCHAR(50) NOT NULL, -- Train, Metro, Highway
    start_point VARCHAR(100),
    end_point VARCHAR(100),
    coverage_quality VARCHAR(20), -- Good, Variable, Poor
    known_issues TEXT
)


Table: building_types
------------------------------
CREATE TABLE building_types (
    building_type_id VARCHAR(50) PRIMARY KEY,
    building_category VARCHAR(100) NOT NULL, -- Apartment, Office, Basement, etc.
    construction_material VARCHAR(100), -- Concrete, Wood, etc.
    avg_signal_reduction_percent INT,
    recommended_solutions TEXT
)


Table: common_network_issues
------------------------------
CREATE TABLE common_network_issues (
    issue_id VARCHAR(50) PRIMARY KEY,
    issue_category VARCHAR(50) NOT NULL,
    issue_description TEXT NOT NULL,
    affected_technologies VARCHAR(100),
    affected_services VARCHAR(100),
    typical_symptoms TEXT,
    troubleshooting_steps TEXT,
    resolution_approach TEXT
)


Table: device_compatibility
------------------------------
CREATE TABLE device_compatibility (
    compatibility_id VARCHAR(50) PRIMARY KEY,
    device_make VARCHAR(100) NOT NULL,
    device_model VARCHAR(100) NOT NULL,
    os_version VARCHAR(50),
    network_technology VARCHAR(20), -- 4G, 5G, etc.
    known_issues TEXT,
    recommended_settings TEXT,
    last_updated TIMESTAMP
)
