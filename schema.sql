-- Travel Agency System Schema
-- Based on ER Diagram

-- 1. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone_number TEXT,
    loyalty_points INTEGER DEFAULT 0
);

-- 2. Package Tours Table
CREATE TABLE IF NOT EXISTS package_tours (
    package_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    destination TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    base_price REAL,
    max_capacity INTEGER,
    tour_type TEXT,
    description TEXT
);

-- 3. Guides Table
CREATE TABLE IF NOT EXISTS guides (
    guide_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    languages_spoken TEXT,
    contact_info TEXT,
    availability_status TEXT,
    experience_years INTEGER,
    rating REAL,
    specialization TEXT
);

-- 4. Transport Table
CREATE TABLE IF NOT EXISTS transport (
    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    capacity INTEGER,
    plate_number TEXT UNIQUE,
    driver_name TEXT,
    route_info TEXT
);

-- 5. Reservations Table
CREATE TABLE IF NOT EXISTS reservations (
    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    number_of_people INTEGER,
    total_price REAL,
    reservation_status TEXT,
    special_request TEXT,
    booking_channel TEXT,
    assignment_date DATE,
    customer_id INTEGER,
    package_id INTEGER,
    guide_id INTEGER,
    vehicle_id INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (package_id) REFERENCES package_tours(package_id),
    FOREIGN KEY (guide_id) REFERENCES guides(guide_id),
    FOREIGN KEY (vehicle_id) REFERENCES transport(vehicle_id)
);

-- 6. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    reservation_id INTEGER,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    payment_method TEXT,
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    transaction_id TEXT UNIQUE,
    status TEXT,
    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id)
);

-- 7. Many-to-Many Relationship: PackageTour eligible for Guide
CREATE TABLE IF NOT EXISTS packagetour_guide_eligibility (
    package_id INTEGER,
    guide_id INTEGER,
    PRIMARY KEY (package_id, guide_id),
    FOREIGN KEY (package_id) REFERENCES package_tours(package_id),
    FOREIGN KEY (guide_id) REFERENCES guides(guide_id)
);

-- Sample Data for testing
INSERT INTO customers (name, email, phone_number, loyalty_points) VALUES ('Alice Smith', 'alice@email.com', '555-0101', 150);
INSERT INTO package_tours (title, destination, base_price) VALUES ('Paris Getaway', 'France', 1200.00);
INSERT INTO guides (name, specialization) VALUES ('Jean-Pierre', 'History');
INSERT INTO transport (type, plate_number, driver_name) VALUES ('Minibus', 'ABC-123', 'John Doe');
