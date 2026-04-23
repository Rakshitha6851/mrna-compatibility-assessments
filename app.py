from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import random
import smtplib
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-prod')

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
@app.route('/forgot.html')
def forgot():
    return render_template('forgot.html')

# ---------- AUTH ----------
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = (data['email'] or '').strip().lower()

    if email in users:
        return jsonify({"message": "User already exists"}), 400

    users[email] = {
        "name": data['name'],
        "password": data['password']
    }

    return jsonify({"message": "Account created"})


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = (data['email'] or '').strip().lower()
    password = data['password']

    print(f"[DEBUG] Login attempt: email='{email}', received_pw='{password}'")
    user = users.get(email)
    if user:
        print(f"[DEBUG] Stored user: pw='{user['password']}'")
    else:
        print("[DEBUG] No user found for email")

    if user and user['password'].lower() == password.lower():
        session['user_email'] = email
        session['user_name'] = user['name']
        print(f"[DEBUG] Login SUCCESS for {email}")
        return jsonify({"message": "Login success", "name": user['name']})
    print(f"[DEBUG] Login FAILED for {email}")
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

    email = (data.get('email') or '').strip().lower()

    print("USERS:", users)

    if not email:
        return jsonify({"message": "Email is required"}), 400

    if email not in users:
        return jsonify({"message": "Email not registered"}), 400

    otp = str(random.randint(100000, 999999))
    otp_storage[email] = otp

    try:
        send_email(email, otp)
    except Exception as e:
        print("Failed to send OTP email:", repr(e))
        return jsonify({"message": "Failed to send OTP. Check email credentials or SMTP setup."}), 500

    return jsonify({"message": "OTP sent"})


@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = (data['email'] or '').strip().lower()
    otp = data['otp']

    if otp_storage.get(email) == otp:
        return jsonify({"message": "Verified"})
    return jsonify({"message": "Invalid OTP"}), 400


@app.route('/dashboard')
def dashboard():
    if not session.get('user_email'):
        return redirect(url_for('home'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = (data['email'] or '').strip().lower()
    password = data['password'].strip().lower()

    if email in users:
        users[email]['password'] = password
        print(f"[DEBUG] Password reset for {email}")
        return jsonify({"message": "Password updated"})
    return jsonify({"message": "User not found"}), 400

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
