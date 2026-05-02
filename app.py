from flask import Flask, render_template, request, redirect
import mysql.connector
import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "travel_agency")
    )
    return connection

@app.route('/')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT COUNT(*) as count FROM customers')
    total_customers = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM package_tours')
    total_tours = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM reservations')
    total_reservations = cursor.fetchone()['count']

    cursor.execute('SELECT SUM(amount) as revenue FROM payments')
    total_revenue = cursor.fetchone()['revenue'] or 0

    query_recent = '''
        SELECT r.reservation_id, c.name as customer_name, p.title as tour_title, r.booking_date
        FROM reservations r
        JOIN customers c ON r.customer_id = c.customer_id
        JOIN package_tours p ON r.package_id = p.package_id
        ORDER BY r.booking_date DESC LIMIT 5
    '''
    cursor.execute(query_recent)
    recent_bookings = cursor.fetchall()

    query_dest = '''
        SELECT destination, COUNT(*) as bookings
        FROM reservations r
        JOIN package_tours p ON r.package_id = p.package_id
        GROUP BY destination ORDER BY bookings DESC LIMIT 3
    '''
    cursor.execute(query_dest)
    top_destinations = cursor.fetchall()

    cursor.close()
    conn.close()

    stats = {
        'total_customers': total_customers,
        'total_tours': total_tours,
        'total_reservations': total_reservations,
        'total_revenue': total_revenue,
        'recent_bookings': recent_bookings,
        'top_destinations': top_destinations
    }
    return render_template('dashboard.html', stats=stats)

@app.route('/customers')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM customers')
    customers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', customers=customers)

@app.route('/add_customer', methods=['POST'])
def add_customer():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO customers (name, email, phone_number) VALUES (%s, %s, %s)',
        (name, email, phone)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/customers')

@app.route('/delete_customer/<int:id>')
def delete_customer(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM customers WHERE customer_id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/customers')

@app.route('/edit_customer/<int:id>', methods=['GET', 'POST'])
def edit_customer(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        cursor.execute(
            'UPDATE customers SET name=%s, email=%s, phone_number=%s WHERE customer_id=%s',
            (name, email, phone, id)
        )
        conn.commit()
        conn.close()
        return redirect('/customers')

    cursor.execute('SELECT * FROM customers WHERE customer_id = %s', (id,))
    customer = cursor.fetchone()
    conn.close()
    return render_template('edit_customer.html', customer=customer)

@app.route('/tours')
def tours():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM package_tours')
    tours = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('tours.html', tours=tours)

@app.route('/add_tour', methods=['POST'])
def add_tour():
    title = request.form.get('title')
    destination = request.form.get('destination')
    price = request.form.get('price')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    capacity = request.form.get('capacity')
    tour_type = request.form.get('tour_type')
    description = request.form.get('description')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO package_tours (title, destination, base_price, start_date, end_date, max_capacity, tour_type, description) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
        (title, destination, price, start_date, end_date, capacity, tour_type, description)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/tours')

@app.route('/delete_tour/<int:id>')
def delete_tour(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM package_tours WHERE package_id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/tours')

@app.route('/reservations')
def reservations():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = '''
        SELECT r.reservation_id, r.booking_date, r.reservation_status, r.number_of_people, r.special_request,
               r.booking_channel, r.assignment_date,
               c.name as customer_name, p.title as tour_title, 
               g.name as guide_name, t.type as vehicle_type, t.plate_number
        FROM reservations r
        JOIN customers c ON r.customer_id = c.customer_id
        JOIN package_tours p ON r.package_id = p.package_id
        LEFT JOIN guides g ON r.guide_id = g.guide_id
        LEFT JOIN transport t ON r.vehicle_id = t.vehicle_id
    '''
    cursor.execute(query)
    reservations_list = cursor.fetchall()
    
    cursor.execute('SELECT customer_id, name, email FROM customers')
    customers = cursor.fetchall()
    cursor.execute('SELECT package_id, title, base_price FROM package_tours')
    tours = cursor.fetchall()
    cursor.execute('SELECT guide_id, name FROM guides')
    guides = cursor.fetchall()
    cursor.execute('SELECT vehicle_id, type, plate_number FROM transport')
    transport = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('reservations.html', 
                           reservations=reservations_list, 
                           customers=customers, 
                           tours=tours,
                           guides=guides,
                           transport=transport)

@app.route('/add_reservation', methods=['POST'])
def add_reservation():
    customer_id = request.form.get('customer_id')
    package_id = request.form.get('package_id')
    guide_id = request.form.get('guide_id')
    vehicle_id = request.form.get('vehicle_id')
    people = request.form.get('people')
    request_text = request.form.get('special_request')
    channel = request.form.get('booking_channel')
    assign_date = request.form.get('assignment_date') or date.today()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO reservations (customer_id, package_id, guide_id, vehicle_id, number_of_people, special_request, booking_channel, assignment_date, reservation_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (customer_id, package_id, guide_id, vehicle_id, people, request_text, channel, assign_date, 'Confirmed')
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/reservations')

@app.route('/delete_reservation/<int:id>')
def delete_reservation(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reservations WHERE reservation_id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/reservations')

@app.route('/guides')
def guides():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM guides')
    guides_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('guides.html', guides=guides_list)

@app.route('/add_guide', methods=['POST'])
def add_guide():
    name = request.form.get('name')
    spec = request.form.get('specialization')
    langs = request.form.get('languages')
    exp = request.form.get('experience')
    rating = request.form.get('rating')
    status = request.form.get('status')
    contact = request.form.get('contact_info')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO guides (name, specialization, languages_spoken, experience_years, rating, availability_status, contact_info) VALUES (%s, %s, %s, %s, %s, %s, %s)',
        (name, spec, langs, exp, rating, status, contact)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/guides')

@app.route('/edit_guide/<int:id>', methods=['GET', 'POST'])
def edit_guide(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form.get('name')
        spec = request.form.get('specialization')
        langs = request.form.get('languages')
        exp = request.form.get('experience')
        rating = request.form.get('rating')
        status = request.form.get('status')
        contact = request.form.get('contact_info')
        
        cursor.execute(
            'UPDATE guides SET name=%s, specialization=%s, languages_spoken=%s, experience_years=%s, rating=%s, availability_status=%s, contact_info=%s WHERE guide_id=%s',
            (name, spec, langs, exp, rating, status, contact, id)
        )
        conn.commit()
        conn.close()
        return redirect('/guides')

    cursor.execute('SELECT * FROM guides WHERE guide_id = %s', (id,))
    guide = cursor.fetchone()
    conn.close()
    return render_template('edit_guide.html', guide=guide)

@app.route('/delete_guide/<int:id>')
def delete_guide(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM guides WHERE guide_id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/guides')

@app.route('/transport')
def transport():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM transport')
    transport_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('transport.html', transport=transport_list)

@app.route('/add_transport', methods=['POST'])
def add_transport():
    v_type = request.form.get('type')
    plate = request.form.get('plate')
    driver = request.form.get('driver')
    capacity = request.form.get('capacity')
    route = request.form.get('route')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO transport (type, plate_number, driver_name, capacity, route_info) VALUES (%s, %s, %s, %s, %s)',
        (v_type, plate, driver, capacity, route)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/transport')

@app.route('/edit_transport/<int:id>', methods=['GET', 'POST'])
def edit_transport(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        v_type = request.form.get('type')
        plate = request.form.get('plate')
        driver = request.form.get('driver')
        capacity = request.form.get('capacity')
        route = request.form.get('route')

        cursor.execute(
            'UPDATE transport SET type=%s, plate_number=%s, driver_name=%s, capacity=%s, route_info=%s WHERE vehicle_id=%s',
            (v_type, plate, driver, capacity, route, id)
        )
        conn.commit()
        conn.close()
        return redirect('/transport')

    cursor.execute('SELECT * FROM transport WHERE vehicle_id = %s', (id,))
    vehicle = cursor.fetchone()
    conn.close()
    return render_template('edit_transport.html', vehicle=vehicle)

@app.route('/delete_transport/<int:id>')
def delete_transport(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transport WHERE vehicle_id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/transport')

@app.route('/eligibility')
def eligibility():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = '''
        SELECT p.package_id, g.guide_id, p.title as tour_title, g.name as guide_name, g.specialization
        FROM packagetour_guide_eligibility e
        JOIN package_tours p ON e.package_id = p.package_id
        JOIN guides g ON e.guide_id = g.guide_id
    '''
    cursor.execute(query)
    eligibility_list = cursor.fetchall()
    
    cursor.execute('SELECT package_id, title, destination FROM package_tours')
    tours = cursor.fetchall()
    cursor.execute('SELECT guide_id, name, specialization FROM guides')
    guides = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('eligibility.html', 
                           eligibility=eligibility_list, 
                           tours=tours, 
                           guides=guides)

@app.route('/add_eligibility', methods=['POST'])
def add_eligibility():
    package_id = request.form.get('package_id')
    guide_id = request.form.get('guide_id')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO packagetour_guide_eligibility (package_id, guide_id) VALUES (%s, %s)',
            (package_id, guide_id)
        )
        conn.commit()
    except:
        pass
    finally:
        cursor.close()
        conn.close()
    return redirect('/eligibility')

@app.route('/delete_eligibility/<int:tour_id>/<int:guide_id>')
def delete_eligibility(tour_id, guide_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM packagetour_guide_eligibility WHERE package_id = %s AND guide_id = %s', 
        (tour_id, guide_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/eligibility')

@app.route('/payments')
def payments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('SELECT * FROM payments ORDER BY payment_date DESC')
    payments_list = cursor.fetchall()
    
    query = '''
        SELECT r.reservation_id, c.name as customer_name, p.title as tour_title
        FROM reservations r
        JOIN customers c ON r.customer_id = c.customer_id
        JOIN package_tours p ON r.package_id = p.package_id
    '''
    cursor.execute(query)
    reservations_list = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('payments.html', 
                           payments=payments_list, 
                           reservations=reservations_list)

@app.route('/add_payment', methods=['POST'])
def add_payment():
    res_id = request.form.get('reservation_id')
    amount = request.form.get('amount')
    method = request.form.get('method')
    currency = request.form.get('currency') or 'USD'
    tx_id = request.form.get('transaction_id')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO payments (reservation_id, amount, payment_method, currency, transaction_id, status) VALUES (%s, %s, %s, %s, %s, %s)',
        (res_id, amount, method, currency, tx_id, 'Completed')
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/payments')

if __name__ == '__main__':
    app.run(debug=True)
