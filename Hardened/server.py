from flask import Flask, request, render_template
import pymysql
from datetime import datetime, timedelta
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import requests
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
import re

app = Flask(__name__)

load_dotenv()

RECAPTCHA_SECRET = os.getenv("RECAPTCHA_SECRET")
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")
ALERT_EMAIL_PASSWORD = os.getenv("ALERT_EMAIL_PASSWORD")

ph = PasswordHasher()

# Track failed attempts by username and IP
failed_attempts = {}          # {username: [timestamps]}
failed_attempts_ip = {}       # {ip: [timestamps]}

LOCKOUT_THRESHOLD = 5
LOCKOUT_DURATION = timedelta(minutes=15)

def get_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="credentials"
    )

def valid_password(pw):
    return (
        len(pw) >= 8 and
        re.search(r"[A-Z]", pw) and
        re.search(r"[a-z]", pw) and
        re.search(r"[0-9]", pw) and
        re.search(r"[^A-Za-z0-9]", pw)
    )

def record_failed_attempt(username, ip):
    now = datetime.now()

    if username not in failed_attempts:
        failed_attempts[username] = []
    failed_attempts[username].append(now)

    if ip not in failed_attempts_ip:
        failed_attempts_ip[ip] = []
    failed_attempts_ip[ip].append(now)

def clear_attempts(username, ip):
    if username in failed_attempts:
        failed_attempts[username] = []
    if ip in failed_attempts_ip:
        failed_attempts_ip[ip] = []

def is_locked_out(username, ip):
    cutoff = datetime.now() - LOCKOUT_DURATION

    if username in failed_attempts:
        failed_attempts[username] = [t for t in failed_attempts[username] if t > cutoff]
        if len(failed_attempts[username]) >= LOCKOUT_THRESHOLD:
            return True

    if ip in failed_attempts_ip:
        failed_attempts_ip[ip] = [t for t in failed_attempts_ip[ip] if t > cutoff]
        if len(failed_attempts_ip[ip]) >= LOCKOUT_THRESHOLD:
            return True

    return False

def hash_password(password):
    return ph.hash(password)

def check_password(password, hashed):
    try:
        return ph.verify(hashed, password)
    except VerifyMismatchError:
        return False

@app.route("/")
def home():
    return render_template("index.html", error=None)

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    ip = request.remote_addr

    if is_locked_out(username, ip):
        return render_template("index.html", error="Too many failed attempts. Try again in 15 minutes.")

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        result = cursor.fetchone()

        if result and check_password(password, result[2]):
            clear_attempts(username, ip)
            return render_template("message.html", title="Login Successful!", message=f"Welcome, {username}.", show_signup=False)

        record_failed_attempt(username, ip)

        if len(failed_attempts.get(username, [])) < LOCKOUT_THRESHOLD:
            return render_template("index.html", error="Invalid username or password.")
        else:
            return render_template("captcha.html", username=username)

    finally:
        cursor.close()
        db.close()

@app.route("/captcha", methods=["POST"])
def captcha():
    username = request.form["username"]
    ip = request.remote_addr
    recaptcha_response = request.form["g-recaptcha-response"]

    verify_url = "https://www.google.com/recaptcha/api/siteverify"
    result = requests.post(verify_url, data={
        "secret": RECAPTCHA_SECRET,
        "response": recaptcha_response
    }).json()

    if result.get("success"):
        clear_attempts(username, ip)
        return render_template("index.html", error="CAPTCHA passed. Please log in again.")

    failed_attempts[username] = [datetime.now()] * LOCKOUT_THRESHOLD
    failed_attempts_ip[ip] = [datetime.now()] * LOCKOUT_THRESHOLD

    try:
        msg = MIMEText(
            f"Security Alert:\n\nMultiple failed login attempts detected.\n"
            f"Username: {username}\n"
            f"IP Address: {ip}\n"
            f"Timestamp: {datetime.now()}\n\n"
            f"The account and IP have been locked for 15 minutes."
        )
        msg["Subject"] = "Security Alert: Suspicious Login Activity"
        msg["From"] = ALERT_EMAIL_FROM
        msg["To"] = ALERT_EMAIL_TO

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(ALERT_EMAIL_FROM, ALERT_EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
    except:
        pass

    return render_template("index.html", error="CAPTCHA failed. Account locked for 15 minutes.")

@app.route("/signup-page")
def signup_page():
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"]

    if not valid_password(password):
        return render_template("signup.html", error="Password must contain upper, lower, digit, special char, and be 8+ chars.")

    db = get_db()
    cursor = db.cursor()

    try:
        hashed_password = hash_password(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        db.commit()
        return render_template("message.html", title="Account Created!", message="Your account has been created. You may now log in.", show_signup=False)
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8001, debug=True)
