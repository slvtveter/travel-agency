from flask import Flask, render_template, request, redirect
import mysql.connector
import os
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
    return redirect('/')

@app.route('/delete_customer/<int:id>')
def delete_customer(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM customers WHERE customer_id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/')

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
        return redirect('/')

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

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO package_tours (title, destination, base_price, start_date, end_date, max_capacity) VALUES (%s, %s, %s, %s, %s, %s)',
        (title, destination, price, start_date, end_date, capacity)
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
        SELECT r.reservation_id, r.booking_date, r.reservation_status, 
               c.name as customer_name, p.title as tour_title
        FROM reservations r
        JOIN customers c ON r.customer_id = c.customer_id
        JOIN package_tours p ON r.package_id = p.package_id
    '''
    cursor.execute(query)
    reservations_list = cursor.fetchall()
    
    cursor.execute('SELECT customer_id, name, email FROM customers')
    customers = cursor.fetchall()
    cursor.execute('SELECT package_id, title, base_price FROM package_tours')
    tours = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('reservations.html', 
                           reservations=reservations_list, 
                           customers=customers, 
                           tours=tours)

@app.route('/add_reservation', methods=['POST'])
def add_reservation():
    customer_id = request.form.get('customer_id')
    package_id = request.form.get('package_id')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO reservations (customer_id, package_id, reservation_status) VALUES (%s, %s, %s)',
        (customer_id, package_id, 'Confirmed')
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

if __name__ == '__main__':
    app.run(debug=True)
