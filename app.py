from contextlib import contextmanager
from flask import Flask, abort, flash, render_template, request, redirect
import mysql.connector
import os
import time
from datetime import date
from dotenv import load_dotenv
from mysql.connector import Error as MySQLError, IntegrityError
from werkzeug.exceptions import BadRequest

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

DB_CONNECT_RETRIES = int(os.getenv("DB_CONNECT_RETRIES", "3"))
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "5"))
DB_RETRY_DELAY = float(os.getenv("DB_RETRY_DELAY", "0.5"))
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "TRY")

def get_db_connection():
    last_error = None
    for attempt in range(1, DB_CONNECT_RETRIES + 1):
        try:
            return mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT", "3306")),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                connection_timeout=DB_CONNECT_TIMEOUT,
            )
        except MySQLError as err:
            last_error = err
            if attempt < DB_CONNECT_RETRIES:
                time.sleep(DB_RETRY_DELAY)
    raise ConnectionError("Could not connect to MySQL database.") from last_error


@contextmanager
def db_cursor(dictionary=False, commit=False):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=dictionary)
        yield cursor
        if commit:
            connection.commit()
    except Exception:
        if commit:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


def fetch_all(query, params=()):
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def fetch_one(query, params=()):
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()


def execute_write(query, params=()):
    with db_cursor(commit=True) as cursor:
        cursor.execute(query, params)


def flash_and_return(message, category='danger', status_code=400):
    if request.referrer:
        flash(message, category)
        return redirect(request.referrer)
    return message, status_code


def mysql_error_message(err):
    message = str(err)
    if getattr(err, 'errno', None) == 1062:
        return "A record with this unique value already exists."
    if getattr(err, 'errno', None) == 1406:
        return "One of the submitted values is too long."
    if getattr(err, 'errno', None) == 1048:
        return "A required field is missing."
    if getattr(err, 'errno', None) == 1364:
        return "A required field has no value."
    if getattr(err, 'errno', None) == 1451:
        return "This record cannot be deleted because other records still use it."
    if getattr(err, 'errno', None) == 1452:
        return "One of the selected related records does not exist."
    if getattr(err, 'errno', None) == 3819 or "check constraint" in message.lower():
        return "The submitted data does not satisfy the database rules."
    return "The submitted data could not be saved. Please check the form values."


def parse_positive_int(value, field_name):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        abort(400, description=f"{field_name} must be a positive number.")
    if parsed <= 0:
        abort(400, description=f"{field_name} must be a positive number.")
    return parsed


def calculate_reservation_total(package_id, people):
    tour = fetch_one('SELECT base_price FROM package_tours WHERE package_id = %s', (package_id,))
    if tour is None:
        abort(400, description="Selected package tour does not exist.")
    return tour['base_price'] * people


@app.context_processor
def inject_currency():
    return {'default_currency': DEFAULT_CURRENCY}


@app.errorhandler(ConnectionError)
def handle_connection_error(err):
    app.logger.exception("Database connection failed: %s", err)
    return "Database temporarily unavailable. Please check the local MySQL connection.", 503


@app.errorhandler(BadRequest)
def handle_bad_request(err):
    return flash_and_return(err.description or "Please check the submitted form values.", status_code=400)


@app.errorhandler(IntegrityError)
def handle_integrity_error(err):
    app.logger.warning("Database constraint error: %s", err)
    return flash_and_return(mysql_error_message(err), status_code=409)


@app.errorhandler(MySQLError)
def handle_mysql_error(err):
    app.logger.warning("Database error: %s", err)
    return flash_and_return(mysql_error_message(err), status_code=400)

@app.route('/')
def dashboard():
    with db_cursor(dictionary=True) as cursor:
        cursor.execute('SELECT COUNT(*) as count FROM customers')
        total_customers = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM package_tours')
        total_tours = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM reservations')
        total_reservations = cursor.fetchone()['count']
        cursor.execute('SELECT SUM(amount) as revenue FROM payments')
        total_revenue = cursor.fetchone()['revenue'] or 0
        cursor.execute('''
            SELECT r.reservation_id, c.name as customer_name, p.title as tour_title, r.booking_date
            FROM reservations r
            JOIN customers c ON r.customer_id = c.customer_id
            JOIN package_tours p ON r.package_id = p.package_id
            ORDER BY r.booking_date DESC LIMIT 5
        ''')
        recent_bookings = cursor.fetchall()
        cursor.execute('''
            SELECT destination, COUNT(*) as bookings
            FROM reservations r
            JOIN package_tours p ON r.package_id = p.package_id
            GROUP BY destination ORDER BY bookings DESC LIMIT 3
        ''')
        top_destinations = cursor.fetchall()
    stats = {
        'total_customers': total_customers,
        'total_tours': total_tours,
        'total_reservations': total_reservations,
        'total_revenue': total_revenue,
        'recent_bookings': recent_bookings,
        'top_destinations': top_destinations
    }
    return render_template('dashboard.html', stats=stats)


@app.route('/health')
def health():
    fetch_one('SELECT 1 AS ok')
    return {'status': 'ok'}, 200

@app.route('/customers')
def customers():
    customers_list = fetch_all('SELECT * FROM customers')
    return render_template('index.html', customers=customers_list)

@app.route('/add_customer', methods=['POST'])
def add_customer():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    loyalty_points = request.form.get('loyalty_points') or 0
    execute_write('INSERT INTO customers (name, email, phone_number, loyalty_points) VALUES (%s, %s, %s, %s)', (name, email, phone, loyalty_points))
    return redirect('/customers')

@app.route('/edit_customer/<int:id>', methods=['GET', 'POST'])
def edit_customer(id):
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        loyalty_points = request.form.get('loyalty_points') or 0
        execute_write('UPDATE customers SET name=%s, email=%s, phone_number=%s, loyalty_points=%s WHERE customer_id=%s', (name, email, phone, loyalty_points, id))
        return redirect('/customers')
    customer = fetch_one('SELECT * FROM customers WHERE customer_id = %s', (id,))
    return render_template('edit_customer.html', customer=customer)

@app.route('/delete_customer/<int:id>')
def delete_customer(id):
    execute_write('DELETE FROM customers WHERE customer_id = %s', (id,))
    return redirect('/customers')

@app.route('/tours')
def tours():
    tours_list = fetch_all('SELECT * FROM package_tours')
    return render_template('tours.html', tours=tours_list)

@app.route('/add_tour', methods=['POST'])
def add_tour():
    title = request.form.get('title')
    destination = request.form.get('destination')
    price = request.form.get('price')
    start_date = request.form.get('start_date') or None
    end_date = request.form.get('end_date') or None
    capacity = request.form.get('capacity') or None
    tour_type = request.form.get('tour_type')
    description = request.form.get('description')
    execute_write('INSERT INTO package_tours (title, destination, base_price, start_date, end_date, max_capacity, tour_type, description) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (title, destination, price, start_date, end_date, capacity, tour_type, description))
    return redirect('/tours')

@app.route('/edit_tour/<int:id>', methods=['GET', 'POST'])
def edit_tour(id):
    if request.method == 'POST':
        title = request.form.get('title')
        destination = request.form.get('destination')
        price = request.form.get('price')
        start_date = request.form.get('start_date') or None
        end_date = request.form.get('end_date') or None
        capacity = request.form.get('capacity') or None
        tour_type = request.form.get('tour_type')
        description = request.form.get('description')
        execute_write('UPDATE package_tours SET title=%s, destination=%s, base_price=%s, start_date=%s, end_date=%s, max_capacity=%s, tour_type=%s, description=%s WHERE package_id=%s', (title, destination, price, start_date, end_date, capacity, tour_type, description, id))
        return redirect('/tours')
    tour = fetch_one('SELECT * FROM package_tours WHERE package_id = %s', (id,))
    return render_template('edit_tour.html', tour=tour)

@app.route('/delete_tour/<int:id>')
def delete_tour(id):
    execute_write('DELETE FROM package_tours WHERE package_id = %s', (id,))
    return redirect('/tours')

@app.route('/guides')
def guides():
    guides_list = fetch_all('SELECT * FROM guides')
    return render_template('guides.html', guides=guides_list)

@app.route('/add_guide', methods=['POST'])
def add_guide():
    name = request.form.get('name')
    spec = request.form.get('specialization')
    langs = request.form.get('languages')
    exp = request.form.get('experience') or None
    rating = request.form.get('rating') or None
    status = request.form.get('status')
    contact = request.form.get('contact_info')
    execute_write('INSERT INTO guides (name, specialization, languages_spoken, experience_years, rating, availability_status, contact_info) VALUES (%s, %s, %s, %s, %s, %s, %s)', (name, spec, langs, exp, rating, status, contact))
    return redirect('/guides')

@app.route('/edit_guide/<int:id>', methods=['GET', 'POST'])
def edit_guide(id):
    if request.method == 'POST':
        name = request.form.get('name')
        spec = request.form.get('specialization')
        langs = request.form.get('languages')
        exp = request.form.get('experience') or None
        rating = request.form.get('rating') or None
        status = request.form.get('status')
        contact = request.form.get('contact_info')
        execute_write('UPDATE guides SET name=%s, specialization=%s, languages_spoken=%s, experience_years=%s, rating=%s, availability_status=%s, contact_info=%s WHERE guide_id=%s', (name, spec, langs, exp, rating, status, contact, id))
        return redirect('/guides')
    guide = fetch_one('SELECT * FROM guides WHERE guide_id = %s', (id,))
    return render_template('edit_guide.html', guide=guide)

@app.route('/delete_guide/<int:id>')
def delete_guide(id):
    execute_write('DELETE FROM guides WHERE guide_id = %s', (id,))
    return redirect('/guides')

@app.route('/transport')
def transport():
    transport_list = fetch_all('SELECT * FROM transport')
    return render_template('transport.html', transport=transport_list)

@app.route('/add_transport', methods=['POST'])
def add_transport():
    v_type = request.form.get('type')
    plate = request.form.get('plate')
    driver = request.form.get('driver_name')
    capacity = request.form.get('capacity') or None
    route = request.form.get('route')
    execute_write('INSERT INTO transport (type, plate_number, driver_name, capacity, route_info) VALUES (%s, %s, %s, %s, %s)', (v_type, plate, driver, capacity, route))
    return redirect('/transport')

@app.route('/edit_transport/<int:id>', methods=['GET', 'POST'])
def edit_transport(id):
    if request.method == 'POST':
        v_type = request.form.get('type')
        plate = request.form.get('plate')
        driver = request.form.get('driver_name') or request.form.get('driver')
        capacity = request.form.get('capacity') or None
        route = request.form.get('route')
        execute_write('UPDATE transport SET type=%s, plate_number=%s, driver_name=%s, capacity=%s, route_info=%s WHERE vehicle_id=%s', (v_type, plate, driver, capacity, route, id))
        return redirect('/transport')
    vehicle = fetch_one('SELECT * FROM transport WHERE vehicle_id = %s', (id,))
    return render_template('edit_transport.html', vehicle=vehicle)

@app.route('/delete_transport/<int:id>')
def delete_transport(id):
    execute_write('DELETE FROM transport WHERE vehicle_id = %s', (id,))
    return redirect('/transport')

@app.route('/reservations')
def reservations():
    with db_cursor(dictionary=True) as cursor:
        cursor.execute('''
            SELECT r.reservation_id, r.booking_date, r.reservation_status, r.number_of_people, r.special_request,
                   r.booking_channel, r.assignment_date,
                   c.name as customer_name, p.title as tour_title, 
                   g.name as guide_name, t.type as vehicle_type, t.plate_number
            FROM reservations r
            JOIN customers c ON r.customer_id = c.customer_id
            JOIN package_tours p ON r.package_id = p.package_id
            LEFT JOIN guides g ON r.guide_id = g.guide_id
            LEFT JOIN transport t ON r.vehicle_id = t.vehicle_id
        ''')
        reservations_list = cursor.fetchall()
        cursor.execute('SELECT customer_id, name FROM customers')
        customers_list = cursor.fetchall()
        cursor.execute('SELECT package_id, title FROM package_tours')
        tours_list = cursor.fetchall()
        cursor.execute('SELECT guide_id, name FROM guides')
        guides_list = cursor.fetchall()
        cursor.execute('SELECT vehicle_id, type, plate_number FROM transport')
        transport_list = cursor.fetchall()
    return render_template('reservations.html', reservations=reservations_list, customers=customers_list, tours=tours_list, guides=guides_list, transport=transport_list)

@app.route('/add_reservation', methods=['POST'])
def add_reservation():
    customer_id = request.form.get('customer_id')
    package_id = request.form.get('package_id')
    guide_id = request.form.get('guide_id') or None
    vehicle_id = request.form.get('vehicle_id') or None
    people = parse_positive_int(request.form.get('people'), "People")
    request_text = request.form.get('special_request')
    channel = request.form.get('booking_channel')
    status = request.form.get('status') or 'Pending'
    assign_date = request.form.get('assignment_date') or date.today()
    booking_date = date.today()
    total_price = calculate_reservation_total(package_id, people)
    execute_write('INSERT INTO reservations (booking_date, customer_id, package_id, guide_id, vehicle_id, number_of_people, total_price, special_request, booking_channel, assignment_date, reservation_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (booking_date, customer_id, package_id, guide_id, vehicle_id, people, total_price, request_text, channel, assign_date, status))
    return redirect('/reservations')

@app.route('/edit_reservation/<int:id>', methods=['GET', 'POST'])
def edit_reservation(id):
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        package_id = request.form.get('package_id')
        guide_id = request.form.get('guide_id') or None
        vehicle_id = request.form.get('vehicle_id') or None
        people = parse_positive_int(request.form.get('people'), "People")
        request_text = request.form.get('special_request')
        channel = request.form.get('booking_channel')
        assign_date = request.form.get('assignment_date') or None
        status = request.form.get('status')
        total_price = calculate_reservation_total(package_id, people)
        execute_write('UPDATE reservations SET customer_id=%s, package_id=%s, guide_id=%s, vehicle_id=%s, number_of_people=%s, total_price=%s, special_request=%s, booking_channel=%s, assignment_date=%s, reservation_status=%s WHERE reservation_id=%s', (customer_id, package_id, guide_id, vehicle_id, people, total_price, request_text, channel, assign_date, status, id))
        return redirect('/reservations')
    with db_cursor(dictionary=True) as cursor:
        cursor.execute('SELECT * FROM reservations WHERE reservation_id = %s', (id,))
        res = cursor.fetchone()
        cursor.execute('SELECT customer_id, name FROM customers')
        customers_list = cursor.fetchall()
        cursor.execute('SELECT package_id, title FROM package_tours')
        tours_list = cursor.fetchall()
        cursor.execute('SELECT guide_id, name FROM guides')
        guides_list = cursor.fetchall()
        cursor.execute('SELECT vehicle_id, type, plate_number FROM transport')
        transport_list = cursor.fetchall()
    return render_template('edit_reservation.html', res=res, customers=customers_list, tours=tours_list, guides=guides_list, transport=transport_list)

@app.route('/delete_reservation/<int:id>')
def delete_reservation(id):
    execute_write('DELETE FROM reservations WHERE reservation_id = %s', (id,))
    return redirect('/reservations')

@app.route('/eligibility')
def eligibility():
    with db_cursor(dictionary=True) as cursor:
        cursor.execute('''
            SELECT p.package_id, g.guide_id, p.title as tour_title, g.name as guide_name, g.specialization
            FROM packagetour_guide_eligibility e
            JOIN package_tours p ON e.package_id = p.package_id
            JOIN guides g ON e.guide_id = g.guide_id
        ''')
        eligibility_list = cursor.fetchall()
        cursor.execute('SELECT package_id, title, destination FROM package_tours')
        tours_list = cursor.fetchall()
        cursor.execute('SELECT guide_id, name, specialization FROM guides')
        guides_list = cursor.fetchall()
    return render_template('eligibility.html', eligibility=eligibility_list, tours=tours_list, guides=guides_list)

@app.route('/add_eligibility', methods=['POST'])
def add_eligibility():
    package_id = request.form.get('package_id')
    guide_id = request.form.get('guide_id')
    if not package_id or not guide_id:
        abort(400, description="Package and guide are required.")
    execute_write('INSERT INTO packagetour_guide_eligibility (package_id, guide_id) VALUES (%s, %s)', (package_id, guide_id))
    return redirect('/eligibility')

@app.route('/delete_eligibility/<int:tour_id>/<int:guide_id>')
def delete_eligibility(tour_id, guide_id):
    execute_write('DELETE FROM packagetour_guide_eligibility WHERE package_id = %s AND guide_id = %s', (tour_id, guide_id))
    return redirect('/eligibility')

@app.route('/payments')
def payments():
    with db_cursor(dictionary=True) as cursor:
        cursor.execute('SELECT * FROM payments ORDER BY payment_date DESC')
        payments_list = cursor.fetchall()
        cursor.execute('''
            SELECT r.reservation_id, c.name as customer_name, p.title as tour_title
            FROM reservations r
            JOIN customers c ON r.customer_id = c.customer_id
            JOIN package_tours p ON r.package_id = p.package_id
        ''')
        reservations_list = cursor.fetchall()
    return render_template('payments.html', payments=payments_list, reservations=reservations_list)

@app.route('/add_payment', methods=['POST'])
def add_payment():
    res_id = request.form.get('reservation_id')
    amount = request.form.get('amount')
    method = request.form.get('method')
    currency = request.form.get('currency') or DEFAULT_CURRENCY
    tx_id = request.form.get('transaction_id')
    execute_write('INSERT INTO payments (reservation_id, amount, payment_method, currency, payment_date, transaction_id, status) VALUES (%s, %s, %s, %s, %s, %s, %s)', (res_id, amount, method, currency, date.today(), tx_id, 'Completed'))
    return redirect('/payments')

@app.route('/edit_payment/<int:id>', methods=['GET', 'POST'])
def edit_payment(id):
    if request.method == 'POST':
        res_id = request.form.get('reservation_id')
        amount = request.form.get('amount')
        method = request.form.get('method')
        currency = request.form.get('currency')
        tx_id = request.form.get('transaction_id')
        status = request.form.get('status')
        execute_write('UPDATE payments SET reservation_id=%s, amount=%s, payment_method=%s, currency=%s, transaction_id=%s, status=%s WHERE payment_id=%s', (res_id, amount, method, currency, tx_id, status, id))
        return redirect('/payments')
    with db_cursor(dictionary=True) as cursor:
        cursor.execute('SELECT * FROM payments WHERE payment_id = %s', (id,))
        payment = cursor.fetchone()
        cursor.execute('''
            SELECT r.reservation_id, c.name as customer_name, p.title as tour_title
            FROM reservations r
            JOIN customers c ON r.customer_id = c.customer_id
            JOIN package_tours p ON r.package_id = p.package_id
        ''')
        reservations_list = cursor.fetchall()
    return render_template('edit_payment.html', payment=payment, reservations=reservations_list)

@app.route('/delete_payment/<int:id>')
def delete_payment(id):
    execute_write('DELETE FROM payments WHERE payment_id = %s', (id,))
    return redirect('/payments')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
