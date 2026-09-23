from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from tutor import ask_garona
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# =========================================================
# APP SETTINGS
# =========================================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "garona-ai-secret-key-change-this"
)

FREE_CREDITS = 20
DATABASE = "garona_users.db"


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# Create database when app starts
init_db()


# =========================================================
# LOGIN PAGE
# =========================================================

@app.route("/")
def home():

    if "user_id" in session:
        return redirect("/chat")

    return render_template("login.html")


# =========================================================
# SIGN UP
# =========================================================

@app.route("/signup", methods=["POST"])
def signup():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "Please enter your information."
            }), 400

        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        # Check fields
        if not username:
            return jsonify({
                "success": False,
                "message": "Please enter a username."
            }), 400

        if not email:
            return jsonify({
                "success": False,
                "message": "Please enter your email."
            }), 400

        if not password:
            return jsonify({
                "success": False,
                "message": "Please enter a password."
            }), 400

        if len(password) < 6:
            return jsonify({
                "success": False,
                "message": "Password must be at least 6 characters."
            }), 400

        conn = get_db()

        # Check existing email
        existing_user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_user:

            conn.close()

            return jsonify({
                "success": False,
                "message": "An account with this email already exists."
            }), 409

        # Hash password
        password_hash = generate_password_hash(password)

        # Create user
        cursor = conn.execute(
            """
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
            """,
            (username, email, password_hash)
        )

        user_id = cursor.lastrowid

        conn.commit()
        conn.close()

        # Log user in automatically
        session.clear()

        session["user_id"] = user_id
        session["username"] = username
        session["email"] = email
        session["credits"] = FREE_CREDITS

        session.modified = True

        return jsonify({
            "success": True,
            "message": "Account created successfully.",
            "redirect": "/chat"
        }), 200

    except Exception as e:

        print("\n==============================")
        print("SIGNUP ERROR:")
        print(str(e))
        print("==============================\n")

        return jsonify({
            "success": False,
            "message": "Could not create your account."
        }), 500


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "Please enter your email and password."
            }), 400

        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({
                "success": False,
                "message": "Please enter your email and password."
            }), 400

        conn = get_db()

        user = conn.execute(
            "SELECT id, username, email, password FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user is None:
            return jsonify({
                "success": False,
                "message": "No account was found with this email."
            }), 401

        if not check_password_hash(user["password"], password):
            return jsonify({
                "success": False,
                "message": "Incorrect password."
            }), 401

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["email"] = user["email"]
        session["credits"] = FREE_CREDITS
        session.modified = True

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "redirect": "/chat"
        }), 200

    except Exception as e:
        print("LOGIN ERROR:")
        print(str(e))

        return jsonify({
            "success": False,
            "message": "Login failed. Please try again."
        }), 500

# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================================================
# GARONA AI CHAT PAGE
# =========================================================

@app.route("/chat")
def chat():

    # Must be logged in
    if "user_id" not in session:
        return redirect("/")

    # Give credits if they don't exist
    if "credits" not in session:
        session["credits"] = FREE_CREDITS
        session.modified = True

    return render_template("index.html")


# =========================================================
# ASK GARONA AI
# =========================================================

@app.route("/ask", methods=["POST"])
def ask():

    # Must be logged in
    if "user_id" not in session:

        return jsonify({
            "error": "Please log in first.",
            "login_required": True
        }), 401

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "answer": "Please ask a question."
            }), 400

        question = data.get("question", "").strip()

        if not question:

            return jsonify({
                "answer": "Please ask a question."
            }), 400

        # Create credit account if needed
        if "credits" not in session:

            session["credits"] = FREE_CREDITS
            session.modified = True

        # Check credits
        if session["credits"] <= 0:

            return jsonify({
                "credit_finished": True,
                "credits": 0
            }), 200

        # =================================================
        # CREATOR QUESTIONS
        # =================================================

        creator_questions = [
            "who created you",
            "who made you",
            "who is your creator",
            "who developed you",
            "who built you",
            "who developed garona ai",
            "who created garona ai",
            "who made garona ai",
            "who built garona ai"
        ]

        normalized_question = (
            question.lower()
            .strip()
            .replace("?", "")
            .replace(".", "")
        )

        if normalized_question in creator_questions:

            session["credits"] -= 1
            session.modified = True

            return jsonify({
                "answer":
                    "I was created and developed by Chetangku Rangsa Marak, a B.Sc. Physics student from Garo Hills.",
                "credits":
                    session["credits"]
            }), 200

        # =================================================
        # ASK GEMINI
        # =================================================

        answer = ask_garona(question)

        # Gemini failed
        if answer is None:

            return jsonify({
                "answer":
                    "Garona AI could not connect to Gemini right now. Please check your Gemini API key and the terminal for the exact error."
            }), 500

        # Successful answer
        session["credits"] -= 1
        session.modified = True

        return jsonify({
            "answer": answer,
            "credits": session["credits"]
        }), 200

    except Exception as e:

        print("\n==============================")
        print("APP ERROR:")
        print(str(e))
        print("==============================\n")

        return jsonify({
            "answer":
                "Garona AI encountered a problem. Check the VS Code terminal."
        }), 500


# =========================================================
# UPGRADE PAGE
# =========================================================

@app.route("/upgrade")
def upgrade():

    # Must be logged in
    if "user_id" not in session:
        return redirect("/")

    return """
    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="UTF-8">

        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <title>Upgrade Garona AI</title>

        <style>

            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f7f9fc;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                text-align: center;
            }

            .box {
                background: white;
                padding: 40px 30px;
                border-radius: 20px;
                max-width: 400px;
                width: calc(100% - 40px);
                box-shadow: 0 20px 60px rgba(0,0,0,.12);
            }

            .logo {
                width: 65px;
                height: 65px;
                margin: auto;
                border-radius: 18px;
                background: linear-gradient(
                    135deg,
                    #2563eb,
                    #7c3aed
                );
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                font-weight: bold;
            }

            h1 {
                margin-top: 20px;
            }

            p {
                color: #6b7280;
                line-height: 1.6;
            }

            button {
                width: 100%;
                padding: 14px;
                border: none;
                border-radius: 10px;
                background: linear-gradient(
                    135deg,
                    #2563eb,
                    #7c3aed
                );
                color: white;
                font-size: 15px;
                font-weight: bold;
                cursor: pointer;
                margin-top: 15px;
            }

        </style>

    </head>

    <body>

        <div class="box">

            <div class="logo">G</div>

            <h1>Upgrade Garona AI</h1>

            <p>
                You have used all 20 free questions.
            </p>

            <p>
                Upgrade your account to continue
                using Garona AI.
            </p>

            <button onclick="alert('Payment system coming soon.')">
                Continue to Payment
            </button>

            <button
                onclick="window.location.href='/chat'"
                style="
                    background:#e5e7eb;
                    color:#111827;
                "
            >
                Back to Garona AI
            </button>

        </div>

    </body>

    </html>
    """


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    print("")
    print("==============================")
    print("       GARONA AI RUNNING")
    print("==============================")
    print("http://127.0.0.1:5001")
    print("")

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )