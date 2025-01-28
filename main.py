from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import os
import sqlitecloud
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import schedule
import time
import threading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

today = datetime.datetime.today()
week_num = today.isocalendar()[1]

def weeknumberwrite():
    with open('week_number.txt', 'w') as file:
        file.write(f"Week number: {week_num}")

def weeknumbercheck():
    if os.path.exists('week_number.txt'):
        with open('week_number.txt', 'r') as file:
            stored_week_num = int(file.read().strip().split(": ")[1])
            if stored_week_num != week_num:
                return False
            else:
                return True
    else:
        weeknumberwrite()

app = Flask(__name__)

SECRET_KEY = os.getenv('SECRET_KEY')
MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_PORT = int(os.getenv('MAIL_PORT'))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS') == 'True'
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
DATABASE_LOGIN = os.getenv('DATABASE_LOGIN')

app.secret_key = SECRET_KEY
def checkiftaken(seat_id):

        cursor = conn.cursor()
        cursor.execute('SELECT approved FROM bookings WHERE seat_id = ? AND approved = 1', (seat_id,))
        booking = cursor.fetchone()
        if booking:
            return True
        else:
            return False
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

def send_email(subject, recipient, html_content):
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

@app.route('/', methods=['GET', 'POST'])
def home():
    seats = {str(i): "available" for i in range(1, 6)}
    
    cursor = conn.cursor()
    cursor.execute('SELECT seat_id, approved FROM bookings')
    bookings = cursor.fetchall()
    for booking in bookings:
        seats[booking[0]] = "booked" if booking[1] else "pending"
    return render_template('index.html', seats=seats)

@app.route('/book_seat', methods=['POST'])
def book_seat():
    seat_ids = request.form.get('seat_ids').split(',')
    name = request.form.get('name')
    email = request.form.get('email')
    if seat_ids and name and email:
        
        cursor = conn.cursor()
        for seat_id in seat_ids:
            cursor.execute('INSERT INTO bookings (seat_id, name, email, approved) VALUES (?, ?, ?, 0)', (seat_id, name, email))
        conn.commit()
        return jsonify({"status": "success", "seat_ids": seat_ids})
    return jsonify({"status": "error", "message": "Invalid input"})

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        booking_id = request.form.get('booking_id')
        action = request.form.get('action')
        with sqlite3.connect('bookings.db') as conn:
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
    conn = sqlitecloud.connect(DATABASE_LOGIN)
    cursor = conn.cursor()
    cursor.execute('SELECT id, seat_id, name, email, approved FROM bookings')
    bookings = cursor.fetchall()
    return render_template('admin.html', bookings=bookings)

def restart_app():
    os.execv(__file__, ['python'] + sys.argv)

def schedule_restart():
    schedule.every().monday.at("00:00").do(restart_app)
    while True:
        schedule.run_pending()
        time.sleep(10)
@app.route('/cheat', methods=['GET'])
def cheat():
    return render_template('cheat.html')
if __name__ == '__main__':
    global conn
    conn = sqlitecloud.connect(DATABASE_LOGIN)
    if weeknumbercheck() == False:
    
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bookings ')
        conn.commit()
        weeknumberwrite()
    else:
        pass
    init_db()
    threading.Thread(target=schedule_restart).start()
    app.run(debug=False, host="0.0.0.0", port=80)