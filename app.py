from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import random
import smtplib

app = Flask(__name__)
app.secret_key = "digital_twin_secret_key_2024"  # Required for session management

# In-memory storage (replace with DB later)
users = {}
otp_storage = {}

EMAIL = "yourgmail@gmail.com"
APP_PASSWORD = "your_app_password"  # Gmail App Password

# ---------- ROUTES ----------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/forgot')
def forgot():
    return render_template('forgot.html')

# ---------- AUTH ----------
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data['email'].lower().strip()

    if email in users:
        return jsonify({"message": "User already exists"}), 400

    users[email] = {
        "name": data['name'],
        "password": data['password']
    }

    return jsonify({"message": "Account created"})


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    print("LOGIN DATA RECEIVED:", data)
    if not data:
        return jsonify({"message": "No data provided"}), 400
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')

    print("Looking for user:", email)
    print("Available users:", list(users.keys()))

    user = users.get(email)

    if user and user['password'] == password:
        session['user_email'] = email
        session['user_name'] = user['name']
        print("Login successful for:", email)
        return jsonify({"message": "Login success", "name": user['name']})
    print("Login failed for:", email)
    return jsonify({"message": "Invalid credentials"}), 400


# ---------- OTP ----------
def send_email(to_email, otp):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL, APP_PASSWORD)

    message = f"Subject: OTP Verification\n\nYour OTP is {otp}"
    server.sendmail(EMAIL, to_email, message)
    server.quit()


@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json() or request.form
    print("DATA RECEIVED:", data)

    email = data.get('email')

    print("USERS:", users)   # <-- THIS LINE YOU KEEP SKIPPING

    if email not in users:
        return jsonify({"message": "Email not registered"}), 400

    otp = str(random.randint(100000, 999999))
    otp_storage[email] = otp

    send_email(email, otp)
    return jsonify({"message": "OTP sent"})


@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data['email']
    otp = data['otp']

    if otp_storage.get(email) == otp:
        return jsonify({"message": "Verified"})
    return jsonify({"message": "Invalid OTP"}), 400


@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data['email']
    password = data['password']

    if email in users:
        users[email]['password'] = password
        return jsonify({"message": "Password updated"})

    return jsonify({"message": "User not found"}), 400


@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', name=session.get('user_name'), email=session.get('user_email'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/check-session', methods=['GET'])
def check_session():
    if 'user_email' in session:
        return jsonify({"logged_in": True, "name": session.get('user_name'), "email": session.get('user_email')})
    return jsonify({"logged_in": False}), 401


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
