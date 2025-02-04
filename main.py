from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_session import Session
import os
import sqlitecloud
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_apscheduler import APScheduler
import datetime
import sys
from dotenv import load_dotenv

scheduler = APScheduler()
today = datetime.datetime.today()
week_num = today.isocalendar()[1]
# Load environment variables from .env file
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_PORT = int(os.getenv('MAIL_PORT'))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS') == 'True'
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
DATABASE_LOGIN = os.getenv('DATABASE_LOGIN')

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
def weeknumberwrite(): # Write the week number to a file (!Not being used!)
    with open('week_number.txt', 'w') as file:
        file.write(f"Week number: {week_num}")

def weeknumbercheck(): # Check if the week number is the same as the stored week number (!Not being used!)
    if os.path.exists('week_number.txt'):
        with open('week_number.txt', 'r') as file:
            stored_week_num = int(file.read().strip().split(": ")[1])
            if stored_week_num != week_num:
                return False
            else:
                return True
    else:
        weeknumberwrite()


def checkiftaken(seat_id): # Check if seat is already taken
    global conn
    if conn is None or conn.close:
        conn = sqlitecloud.connect(DATABASE_LOGIN)
    cursor = conn.cursor()
    cursor.execute('SELECT approved FROM bookings WHERE seat_id = ? AND approved = 1', (seat_id,))
    booking = cursor.fetchone()
    print("Booking: ", booking)
    return booking is not None

# This function initializes the database
# It is run once when the server starts
def init_db(): 
    
    
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seat_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                approved BOOLEAN DEFAULT 0
            )
        ''')
        if checkiftaken("1") == False:
            cursor.execute('INSERT OR IGNORE INTO bookings (seat_id, name, email, approved) VALUES ("1", "Timothy", "Timothy@timothy.timothy", 1)')
            conn.commit()
        else: 
            pass


def send_email(subject, recipient, html_content): # This function send an email to the booking recipient
    msg = MIMEMultipart()
    msg['From'] = MAIL_USERNAME
    msg['To'] = recipient
    msg['Subject'] = subject
    part = MIMEText(html_content, 'html')
    msg.attach(part)

    try:
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            if MAIL_USE_TLS:
                server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_USERNAME, recipient, msg.as_string())
    except Exception as e:
        print(f"Failed to send email: {e}")


@app.route('/', methods=['GET', 'POST']) # This is the booking page
def home():
    global conn
    if conn is None or conn.close:
        conn = sqlitecloud.connect(DATABASE_LOGIN)

    cursor = conn.cursor()
    cursor.execute('SELECT seat_id, approved FROM bookings')
    bookings = cursor.fetchall()

    seats = {str(i): "available" for i in range(1, 6)}
    for booking in bookings:
        seats[booking[0]] = "booked" if booking[1] else "pending"

    return render_template('index.html', seats=seats)


@app.route('/book_seat', methods=['POST']) # This is the booking page
def book_seat():
    global conn
    if conn is None or conn.close:
        conn = sqlitecloud.connect(DATABASE_LOGIN)
    seat_ids = request.form.get('seat_ids').split(',')
    name = request.form.get('name')
    email = request.form.get('email')
    print(f"Received seat_ids: {seat_ids}, name: {name}, email: {email}")  # Debugging print
    if seat_ids and name and email:
        cursor = conn.cursor()
        for seat_id in seat_ids:
            print(f"Inserting booking for seat_id: {seat_id}, name: {name}, email: {email}")  # Debugging print
            cursor.execute('INSERT INTO bookings (seat_id, name, email, approved) VALUES (?, ?, ?, 0)', (seat_id, name, email))
        conn.commit()
        print("Booking successful")  # Debugging print
        return jsonify({"status": "success", "seat_ids": seat_ids})
    print("Invalid input")  # Debugging print
    return jsonify({"status": "error", "message": "Invalid input"})


@app.route('/admin', methods=['GET', 'POST']) # This is the admin page
def admin():
    if request.method == 'POST':
        booking_id = request.form.get('booking_id')
        action = request.form.get('action')
        global conn
        if conn is None or conn.close:
            conn = sqlitecloud.connect(DATABASE_LOGIN)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,))
        booking = cursor.fetchone()
        if booking:
            if action == 'approve':
                if checkiftaken(booking[1]) == True:
                    print()
                    return render_template('error.html', error_name="Sätet är redan bokat")
                cursor.execute('UPDATE bookings SET approved = 1 WHERE id = ?', (booking_id,))
                conn.commit()
                send_email(
                    'Bokning godkänd',
                    booking[3],
                    f"""
                    <html>
                    <body>
                        <p>Hej <i>{booking[2]}</i>!</p>
                        <p>Din bokning för säte {booking[1]} har blivit godkänd.</p>
                        <p>Var god kontakta +46 73-328 16 89 för mer information.
                        <br><strong>Kontakta inte denna epostadress.</strong></p>
                    </body>
                    </html>
                    """
                )
            elif action == 'reject':
                cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
                conn.commit()
                send_email(
                    'Bokning avvisad',
                    booking[3],
                    f"""
                    <html>
                    <body>

                        <p>Hej <i>{booking[2]}</i>!</p>
                        <p>Din bokning för säte {booking[1]} har blivit nekad.</p>
                        <p>Var god kontakta +46 73-328 16 89 för mer information.
                        <br><strong>Kontakta inte denna epostadress.</strong></p>
                    </body>
                    </html>
                    """
                )
    elif request.method == 'GET':
        if session.get("logged_in"):
            conn = sqlitecloud.connect(DATABASE_LOGIN)
            cursor = conn.cursor()
            cursor.execute('SELECT id, seat_id, name, email, approved FROM bookings')
            bookings = cursor.fetchall()
            return render_template('admin.html', bookings=bookings)
        else:
            return redirect(url_for('login'))
    else:
        return render_template('error.html', error_name="Fel metod")


# Work in progress
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        
        password = request.form.get('password')
        if password == os.getenv('ADMIN_PASSWORD'):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('error.html', error_name="Fel lösenord")
    elif request.method == 'GET':
        if session.get("logged_in"):
            return redirect(url_for('admin'))
        else:
            return render_template('login.html')
    else:
        return render_template('error.html', error_name="Fel metod")    



def clear_database(): # This function clears the database
    DATABASE_LOGIN = os.getenv('DATABASE_LOGIN')
    conn = sqlitecloud.connect(DATABASE_LOGIN)
    cursor = conn.cursor()

    # Retrieve all user-defined tables (skip system tables)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()

    # Delete all rows from each table except those with seat_id = 1
    for table in tables:
        table_name = table[0]
        cursor.execute(f"DELETE FROM {table_name} WHERE seat_id != 1")

    conn.commit()
    print("All data cleared from the tables except rows with seat_id = 1, but the table structures remain intact.")
    conn.close()


@app.route('/cheat', methods=['GET']) # This is the cheat sheet for the admin
def cheat():
    return render_template('cheat.html') 

scheduler.init_app(app)
scheduler.start()

@scheduler.task('cron', id='cleardatabase', day_of_week='sun', hour=0, minute=0, misfire_grace_time=120)
def cleardatabase():
    clear_database()
    
    

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_name="Sidan kunde inte hittas"), 404
@app.errorhandler(500)
def internal_server_error(e):
    error_message = str(e)
    send_email(
        'Internal Server Error',
        'Liam@suorsa.se',
        f"""
        <html>
        <body>
            <p>Hej Admin!</p>
            <p>Det har uppstått ett internt serverfel.</p>
            <p>Felmeddelande: {error_message}</p>
        </body>
        </html>
        """
    )
    return render_template('error.html', error_name="Något gick fel"), 500




if __name__ == '__main__':
    global conn
    conn = sqlitecloud.connect(DATABASE_LOGIN)
    init_db()
    app.run(debug=True, host="0.0.0.0", port=80)