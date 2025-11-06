from flask import Flask, request, render_template
import pymysql
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

app = Flask(__name__)

# Argon2id Password Hasher
ph = PasswordHasher()  # Uses Argon2id by default

def get_db():
    """Create a new database connection for each request"""
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="vulnerable_credentials"
    )

@app.route("/")
def home():
    return render_template("index.html", error=None)

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    cursor = get_db().cursor()
    
    try:
        query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
        print(f"Executing query: {query}")  # Debug: see the actual query
        cursor.execute(query)
        result = cursor.fetchone()

        if result:
            return render_template(
                "message.html",
                title="Login successful!",
                message=f"Welcome, {username}.",
                show_signup=False
            )
        else:
            return render_template(
                "index.html",
                error=f"Incorrect credentials. Try again. "
            )
    except Exception as e:
        print(f"Error: {e}")  # Debug: see what went wrong
        return f"Error occurred: {str(e)}"  # Or return generic error message

@app.route("/signup-page")
def signup_page():
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"]

    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        db.commit()
        return render_template(
            "message.html",
            title="Account Created!",
            message="Your account has been successfully created. You may now log in.",
            show_signup=False
        )
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)