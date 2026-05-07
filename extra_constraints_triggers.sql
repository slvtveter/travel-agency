USE railway;

DROP PROCEDURE IF EXISTS ensure_check_constraint;
DROP TRIGGER IF EXISTS bi_customers_normalize;
DROP TRIGGER IF EXISTS bu_customers_normalize;
DROP TRIGGER IF EXISTS bi_package_tours_normalize;
DROP TRIGGER IF EXISTS bu_package_tours_normalize;
DROP TRIGGER IF EXISTS bi_guides_normalize;
DROP TRIGGER IF EXISTS bu_guides_normalize;
DROP TRIGGER IF EXISTS bi_transport_normalize;
DROP TRIGGER IF EXISTS bu_transport_normalize;
DROP TRIGGER IF EXISTS bi_reservations_validate;
DROP TRIGGER IF EXISTS bu_reservations_validate;
DROP TRIGGER IF EXISTS bi_payments_validate;
DROP TRIGGER IF EXISTS bu_payments_validate;

DELIMITER $$

CREATE PROCEDURE ensure_check_constraint(
    IN p_table_name VARCHAR(64),
    IN p_constraint_name VARCHAR(64),
    IN p_add_sql TEXT
)
BEGIN
    DECLARE v_exists INT DEFAULT 0;

    SELECT COUNT(*)
    INTO v_exists
    FROM information_schema.table_constraints
    WHERE table_schema = DATABASE()
      AND table_name = p_table_name
      AND constraint_name = p_constraint_name
      AND constraint_type = 'CHECK';

    IF v_exists > 0 THEN
        SET @drop_sql = CONCAT(
            'ALTER TABLE `', p_table_name, '` DROP CHECK `', p_constraint_name, '`'
        );
        PREPARE stmt FROM @drop_sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;

    SET @add_sql = p_add_sql;
    PREPARE stmt FROM @add_sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END$$

CREATE TRIGGER bi_customers_normalize
BEFORE INSERT ON customers
FOR EACH ROW
BEGIN
    SET NEW.name = CONCAT(UPPER(LEFT(TRIM(NEW.name), 1)), SUBSTRING(TRIM(NEW.name), 2));
    SET NEW.email = LOWER(TRIM(NEW.email));

    IF NEW.phone_number IS NOT NULL THEN
        SET NEW.phone_number = REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(TRIM(NEW.phone_number), ' ', ''),
                    '-', ''),
                '(', ''),
            ')', ''),
        '+', '');
    END IF;
END$$

CREATE TRIGGER bu_customers_normalize
BEFORE UPDATE ON customers
FOR EACH ROW
BEGIN
    SET NEW.name = CONCAT(UPPER(LEFT(TRIM(NEW.name), 1)), SUBSTRING(TRIM(NEW.name), 2));
    SET NEW.email = LOWER(TRIM(NEW.email));

    IF NEW.phone_number IS NOT NULL THEN
        SET NEW.phone_number = REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(TRIM(NEW.phone_number), ' ', ''),
                    '-', ''),
                '(', ''),
            ')', ''),
        '+', '');
    END IF;
END$$

CREATE TRIGGER bi_package_tours_normalize
BEFORE INSERT ON package_tours
FOR EACH ROW
BEGIN
    SET NEW.title = CONCAT(UPPER(LEFT(TRIM(NEW.title), 1)), SUBSTRING(TRIM(NEW.title), 2));
    SET NEW.destination = CONCAT(UPPER(LEFT(TRIM(NEW.destination), 1)), SUBSTRING(TRIM(NEW.destination), 2));

    IF NEW.tour_type IS NOT NULL THEN
        SET NEW.tour_type = CONCAT(UPPER(LEFT(TRIM(NEW.tour_type), 1)), SUBSTRING(TRIM(NEW.tour_type), 2));
    END IF;

    IF NEW.description IS NOT NULL THEN
        SET NEW.description = TRIM(NEW.description);
    END IF;
END$$

CREATE TRIGGER bu_package_tours_normalize
BEFORE UPDATE ON package_tours
FOR EACH ROW
BEGIN
    SET NEW.title = CONCAT(UPPER(LEFT(TRIM(NEW.title), 1)), SUBSTRING(TRIM(NEW.title), 2));
    SET NEW.destination = CONCAT(UPPER(LEFT(TRIM(NEW.destination), 1)), SUBSTRING(TRIM(NEW.destination), 2));

    IF NEW.tour_type IS NOT NULL THEN
        SET NEW.tour_type = CONCAT(UPPER(LEFT(TRIM(NEW.tour_type), 1)), SUBSTRING(TRIM(NEW.tour_type), 2));
    END IF;

    IF NEW.description IS NOT NULL THEN
        SET NEW.description = TRIM(NEW.description);
    END IF;
END$$

CREATE TRIGGER bi_guides_normalize
BEFORE INSERT ON guides
FOR EACH ROW
BEGIN
    SET NEW.name = CONCAT(UPPER(LEFT(TRIM(NEW.name), 1)), SUBSTRING(TRIM(NEW.name), 2));

    IF NEW.specialization IS NOT NULL THEN
        SET NEW.specialization = CONCAT(UPPER(LEFT(TRIM(NEW.specialization), 1)), SUBSTRING(TRIM(NEW.specialization), 2));
    END IF;

    IF NEW.contact_info IS NOT NULL THEN
        SET NEW.contact_info = TRIM(NEW.contact_info);
    END IF;
END$$

CREATE TRIGGER bu_guides_normalize
BEFORE UPDATE ON guides
FOR EACH ROW
BEGIN
    SET NEW.name = CONCAT(UPPER(LEFT(TRIM(NEW.name), 1)), SUBSTRING(TRIM(NEW.name), 2));

    IF NEW.specialization IS NOT NULL THEN
        SET NEW.specialization = CONCAT(UPPER(LEFT(TRIM(NEW.specialization), 1)), SUBSTRING(TRIM(NEW.specialization), 2));
    END IF;

    IF NEW.contact_info IS NOT NULL THEN
        SET NEW.contact_info = TRIM(NEW.contact_info);
    END IF;
END$$

CREATE TRIGGER bi_transport_normalize
BEFORE INSERT ON transport
FOR EACH ROW
BEGIN
    SET NEW.type = CONCAT(UPPER(LEFT(TRIM(NEW.type), 1)), SUBSTRING(TRIM(NEW.type), 2));
    SET NEW.plate_number = UPPER(REPLACE(REPLACE(TRIM(NEW.plate_number), ' ', ''), '-', ''));

    IF NEW.driver_name IS NOT NULL THEN
        SET NEW.driver_name = CONCAT(UPPER(LEFT(TRIM(NEW.driver_name), 1)), SUBSTRING(TRIM(NEW.driver_name), 2));
    END IF;

    IF NEW.route_info IS NOT NULL THEN
        SET NEW.route_info = TRIM(NEW.route_info);
    END IF;
END$$

CREATE TRIGGER bu_transport_normalize
BEFORE UPDATE ON transport
FOR EACH ROW
BEGIN
    SET NEW.type = CONCAT(UPPER(LEFT(TRIM(NEW.type), 1)), SUBSTRING(TRIM(NEW.type), 2));
    SET NEW.plate_number = UPPER(REPLACE(REPLACE(TRIM(NEW.plate_number), ' ', ''), '-', ''));

    IF NEW.driver_name IS NOT NULL THEN
        SET NEW.driver_name = CONCAT(UPPER(LEFT(TRIM(NEW.driver_name), 1)), SUBSTRING(TRIM(NEW.driver_name), 2));
    END IF;

    IF NEW.route_info IS NOT NULL THEN
        SET NEW.route_info = TRIM(NEW.route_info);
    END IF;
END$$

CREATE TRIGGER bi_reservations_validate
BEFORE INSERT ON reservations
FOR EACH ROW
BEGIN
    DECLARE v_vehicle_capacity INT DEFAULT NULL;
    DECLARE v_eligible_count INT DEFAULT 0;

    IF NEW.reservation_status IS NULL OR TRIM(NEW.reservation_status) = '' THEN
        SET NEW.reservation_status = 'Pending';
    ELSE
        SET NEW.reservation_status = TRIM(NEW.reservation_status);
    END IF;

    IF NEW.booking_channel IS NOT NULL THEN
        SET NEW.booking_channel = TRIM(NEW.booking_channel);
    END IF;

    IF NEW.assignment_date IS NOT NULL AND NEW.assignment_date < NEW.booking_date THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'assignment_date cannot be earlier than booking_date';
    END IF;

    IF NEW.guide_id IS NOT NULL THEN
        SELECT COUNT(*)
        INTO v_eligible_count
        FROM packagetour_guide_eligibility
        WHERE package_id = NEW.package_id
          AND guide_id = NEW.guide_id;

        IF v_eligible_count = 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Selected guide is not eligible for the chosen package';
        END IF;
    END IF;

    IF NEW.vehicle_id IS NOT NULL THEN
        SELECT capacity
        INTO v_vehicle_capacity
        FROM transport
        WHERE vehicle_id = NEW.vehicle_id;

        IF v_vehicle_capacity IS NULL THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Selected transport vehicle was not found';
        END IF;

        IF NEW.number_of_people > v_vehicle_capacity THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Vehicle capacity is smaller than the reservation size';
        END IF;
    END IF;
END$$

CREATE TRIGGER bu_reservations_validate
BEFORE UPDATE ON reservations
FOR EACH ROW
BEGIN
    DECLARE v_vehicle_capacity INT DEFAULT NULL;
    DECLARE v_eligible_count INT DEFAULT 0;

    IF NEW.reservation_status IS NULL OR TRIM(NEW.reservation_status) = '' THEN
        SET NEW.reservation_status = 'Pending';
    ELSE
        SET NEW.reservation_status = TRIM(NEW.reservation_status);
    END IF;

    IF NEW.booking_channel IS NOT NULL THEN
        SET NEW.booking_channel = TRIM(NEW.booking_channel);
    END IF;

    IF NEW.assignment_date IS NOT NULL AND NEW.assignment_date < NEW.booking_date THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'assignment_date cannot be earlier than booking_date';
    END IF;

    IF NEW.guide_id IS NOT NULL THEN
        SELECT COUNT(*)
        INTO v_eligible_count
        FROM packagetour_guide_eligibility
        WHERE package_id = NEW.package_id
          AND guide_id = NEW.guide_id;

        IF v_eligible_count = 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Selected guide is not eligible for the chosen package';
        END IF;
    END IF;

    IF NEW.vehicle_id IS NOT NULL THEN
        SELECT capacity
        INTO v_vehicle_capacity
        FROM transport
        WHERE vehicle_id = NEW.vehicle_id;

        IF v_vehicle_capacity IS NULL THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Selected transport vehicle was not found';
        END IF;

        IF NEW.number_of_people > v_vehicle_capacity THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Vehicle capacity is smaller than the reservation size';
        END IF;
    END IF;
END$$

CREATE TRIGGER bi_payments_validate
BEFORE INSERT ON payments
FOR EACH ROW
BEGIN
    DECLARE v_total_price DECIMAL(10,2) DEFAULT NULL;

    IF NEW.status IS NULL OR TRIM(NEW.status) = '' THEN
        SET NEW.status = 'Pending';
    ELSE
        SET NEW.status = TRIM(NEW.status);
    END IF;

    IF NEW.currency IS NULL OR TRIM(NEW.currency) = '' THEN
        SET NEW.currency = 'TRY';
    ELSE
        SET NEW.currency = UPPER(TRIM(NEW.currency));
    END IF;

    SET NEW.transaction_id = UPPER(TRIM(NEW.transaction_id));

    SELECT total_price
    INTO v_total_price
    FROM reservations
    WHERE reservation_id = NEW.reservation_id;

    IF v_total_price IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Payment must reference an existing reservation';
    END IF;

    IF NEW.amount <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Payment amount must be greater than zero';
    END IF;

    IF NEW.amount > v_total_price THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Payment amount cannot exceed the reservation total';
    END IF;

    IF NEW.status = 'Completed' AND NEW.amount <> v_total_price THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Completed payments must match the reservation total';
    END IF;
END$$

CREATE TRIGGER bu_payments_validate
BEFORE UPDATE ON payments
FOR EACH ROW
BEGIN
    DECLARE v_total_price DECIMAL(10,2) DEFAULT NULL;

    IF NEW.status IS NULL OR TRIM(NEW.status) = '' THEN
        SET NEW.status = 'Pending';
    ELSE
        SET NEW.status = TRIM(NEW.status);
    END IF;

    IF NEW.currency IS NULL OR TRIM(NEW.currency) = '' THEN
        SET NEW.currency = 'TRY';
    ELSE
        SET NEW.currency = UPPER(TRIM(NEW.currency));
    END IF;

    SET NEW.transaction_id = UPPER(TRIM(NEW.transaction_id));

    SELECT total_price
    INTO v_total_price
    FROM reservations
    WHERE reservation_id = NEW.reservation_id;

    IF v_total_price IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Payment must reference an existing reservation';
    END IF;

    IF NEW.amount <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Payment amount must be greater than zero';
    END IF;

    IF NEW.amount > v_total_price THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Payment amount cannot exceed the reservation total';
    END IF;

    IF NEW.status = 'Completed' AND NEW.amount <> v_total_price THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Completed payments must match the reservation total';
    END IF;
END$$

DELIMITER ;

CALL ensure_check_constraint(
    'customers',
    'chk_customers_name_not_blank',
    'ALTER TABLE `customers` ADD CONSTRAINT `chk_customers_name_not_blank` CHECK (CHAR_LENGTH(TRIM(`name`)) > 0)'
);

CALL ensure_check_constraint(
    'customers',
    'chk_customers_email_format',
    'ALTER TABLE `customers` ADD CONSTRAINT `chk_customers_email_format` CHECK (INSTR(`email`, CHAR(64)) > 1 AND INSTR(SUBSTRING_INDEX(`email`, CHAR(64), -1), CHAR(46)) > 1)'
);

CALL ensure_check_constraint(
    'package_tours',
    'chk_package_title_not_blank',
    'ALTER TABLE `package_tours` ADD CONSTRAINT `chk_package_title_not_blank` CHECK (CHAR_LENGTH(TRIM(`title`)) > 0)'
);

CALL ensure_check_constraint(
    'package_tours',
    'chk_package_destination_not_blank',
    'ALTER TABLE `package_tours` ADD CONSTRAINT `chk_package_destination_not_blank` CHECK (CHAR_LENGTH(TRIM(`destination`)) > 0)'
);

CALL ensure_check_constraint(
    'package_tours',
    'chk_package_type_not_blank',
    'ALTER TABLE `package_tours` ADD CONSTRAINT `chk_package_type_not_blank` CHECK (`tour_type` IS NULL OR CHAR_LENGTH(TRIM(`tour_type`)) > 0)'
);

CALL ensure_check_constraint(
    'guides',
    'chk_guide_name_not_blank',
    'ALTER TABLE `guides` ADD CONSTRAINT `chk_guide_name_not_blank` CHECK (CHAR_LENGTH(TRIM(`name`)) > 0)'
);

CALL ensure_check_constraint(
    'guides',
    'chk_guide_experience_years',
    'ALTER TABLE `guides` ADD CONSTRAINT `chk_guide_experience_years` CHECK (`experience_years` >= 0)'
);

CALL ensure_check_constraint(
    'guides',
    'chk_guide_rating',
    'ALTER TABLE `guides` ADD CONSTRAINT `chk_guide_rating` CHECK (`rating` IS NULL OR (`rating` >= 0 AND `rating` <= 5))'
);

CALL ensure_check_constraint(
    'guides',
    'chk_guide_status_allowed',
    'ALTER TABLE `guides` ADD CONSTRAINT `chk_guide_status_allowed` CHECK (`availability_status` IN (''Available'', ''Busy'', ''On Tour'', ''Vacation''))'
);

CALL ensure_check_constraint(
    'transport',
    'chk_transport_type_not_blank',
    'ALTER TABLE `transport` ADD CONSTRAINT `chk_transport_type_not_blank` CHECK (CHAR_LENGTH(TRIM(`type`)) > 0)'
);

CALL ensure_check_constraint(
    'transport',
    'chk_transport_capacity',
    'ALTER TABLE `transport` ADD CONSTRAINT `chk_transport_capacity` CHECK (`capacity` > 0)'
);

CALL ensure_check_constraint(
    'reservations',
    'chk_number_of_people',
    'ALTER TABLE `reservations` ADD CONSTRAINT `chk_number_of_people` CHECK (`number_of_people` > 0)'
);

CALL ensure_check_constraint(
    'reservations',
    'chk_total_price',
    'ALTER TABLE `reservations` ADD CONSTRAINT `chk_total_price` CHECK (`total_price` >= 0)'
);

CALL ensure_check_constraint(
    'reservations',
    'chk_reservation_status_allowed',
    'ALTER TABLE `reservations` ADD CONSTRAINT `chk_reservation_status_allowed` CHECK (`reservation_status` IN (''Pending'', ''Confirmed'', ''Cancelled''))'
);

CALL ensure_check_constraint(
    'reservations',
    'chk_booking_channel_allowed',
    'ALTER TABLE `reservations` ADD CONSTRAINT `chk_booking_channel_allowed` CHECK (`booking_channel` IS NULL OR `booking_channel` IN (''Website'', ''Mobile App'', ''Phone Call'', ''Walk-in'', ''Online'', ''Agency'', ''Phone''))'
);

CALL ensure_check_constraint(
    'reservations',
    'chk_assignment_date_order',
    'ALTER TABLE `reservations` ADD CONSTRAINT `chk_assignment_date_order` CHECK (`assignment_date` IS NULL OR `assignment_date` >= `booking_date`)'
);

CALL ensure_check_constraint(
    'payments',
    'chk_payment_amount',
    'ALTER TABLE `payments` ADD CONSTRAINT `chk_payment_amount` CHECK (`amount` > 0)'
);

CALL ensure_check_constraint(
    'payments',
    'chk_payment_status_allowed',
    'ALTER TABLE `payments` ADD CONSTRAINT `chk_payment_status_allowed` CHECK (`status` IN (''Pending'', ''Completed'', ''Refunded'', ''Cancelled'', ''Failed''))'
);

CALL ensure_check_constraint(
    'payments',
    'chk_payment_method_allowed',
    'ALTER TABLE `payments` ADD CONSTRAINT `chk_payment_method_allowed` CHECK (`payment_method` IN (''Credit Card'', ''Cash'', ''Bank Transfer'', ''PayPal''))'
);

CALL ensure_check_constraint(
    'payments',
    'chk_currency_allowed',
    'ALTER TABLE `payments` ADD CONSTRAINT `chk_currency_allowed` CHECK (`currency` IS NULL OR `currency` IN (''TRY'', ''USD'', ''EUR'', ''GBP'', ''JPY''))'
);

DROP PROCEDURE IF EXISTS ensure_check_constraint;
