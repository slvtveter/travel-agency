-- Travel Agency System Schema (MySQL Version)

-- 1. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(20),
    loyalty_points INT DEFAULT 0
);

-- 2. Package Tours Table
CREATE TABLE IF NOT EXISTS package_tours (
    package_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    base_price DECIMAL(10, 2),
    max_capacity INT,
    tour_type VARCHAR(100),
    description TEXT
);

-- 3. Guides Table
CREATE TABLE IF NOT EXISTS guides (
    guide_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    languages_spoken TEXT,
    contact_info TEXT,
    availability_status VARCHAR(50),
    experience_years INT,
    rating DECIMAL(3, 2),
    specialization VARCHAR(255)
);

-- 4. Transport Table
CREATE TABLE IF NOT EXISTS transport (
    vehicle_id INT PRIMARY KEY AUTO_INCREMENT,
    type VARCHAR(100) NOT NULL,
    capacity INT,
    plate_number VARCHAR(50) UNIQUE,
    driver_name VARCHAR(255),
    route_info TEXT
);

-- 5. Reservations Table
CREATE TABLE IF NOT EXISTS reservations (
    reservation_id INT PRIMARY KEY AUTO_INCREMENT,
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    number_of_people INT,
    total_price DECIMAL(10, 2),
    reservation_status VARCHAR(50),
    special_request TEXT,
    booking_channel VARCHAR(100),
    assignment_date DATE,
    customer_id INT,
    package_id INT,
    guide_id INT,
    vehicle_id INT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (package_id) REFERENCES package_tours(package_id),
    FOREIGN KEY (guide_id) REFERENCES guides(guide_id),
    FOREIGN KEY (vehicle_id) REFERENCES transport(vehicle_id)
);

-- 6. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    reservation_id INT,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    payment_method VARCHAR(50),
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    transaction_id VARCHAR(100) UNIQUE,
    status VARCHAR(50),
    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id)
);

-- 7. Many-to-Many Relationship: PackageTour eligible for Guide
CREATE TABLE IF NOT EXISTS packagetour_guide_eligibility (
    package_id INT,
    guide_id INT,
    PRIMARY KEY (package_id, guide_id),
    FOREIGN KEY (package_id) REFERENCES package_tours(package_id),
    FOREIGN KEY (guide_id) REFERENCES guides(guide_id)
);

-- Sample Data
INSERT INTO customers (name, email, phone_number, loyalty_points) VALUES ('Alice Smith', 'alice@email.com', '555-0101', 150);
INSERT INTO package_tours (title, destination, base_price) VALUES ('Paris Getaway', 'France', 1200.00);
INSERT INTO guides (name, specialization) VALUES ('Jean-Pierre', 'History');
INSERT INTO transport (type, plate_number, driver_name) VALUES ('Minibus', 'ABC-123', 'John Doe');

select * from customers;
select * from package_tours;
select * from guides;
select * from transport;
