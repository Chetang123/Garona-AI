from flask import Flask, render_template, request, jsonify, session
from tutor import ask_garona

app = Flask(__name__)

# Secret key for sessions
app.secret_key = "garona-ai-secret-key-change-this"

# Free questions per user
FREE_CREDITS = 20


# =========================================================
# LOGIN PAGE
# =========================================================

@app.route("/")
def home():
    return render_template("login.html")


# =========================================================
# GARONA AI CHAT PAGE
# =========================================================

@app.route("/chat")
def chat():

    if "credits" not in session:
        session["credits"] = FREE_CREDITS
        session.modified = True

    return render_template("index.html")


# =========================================================
# ASK GARONA AI
# =========================================================

@app.route("/ask", methods=["POST"])
def ask():

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


        # =================================================
        # CREATE CREDIT ACCOUNT
        # =================================================

        if "credits" not in session:
            session["credits"] = FREE_CREDITS
            session.modified = True


        # =================================================
        # CHECK FREE CREDITS
        # =================================================

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
        # ASK GEMINI THROUGH TUTOR.PY
        # =================================================

        answer = ask_garona(question)


        # =================================================
        # GEMINI FAILED
        # =================================================

        if answer is None:

            return jsonify({
                "answer":
                    "Garona AI could not connect to Gemini right now. Please check your Gemini API key and the terminal for the exact error."
            }), 500


        # =================================================
        # SUCCESS
        # =================================================

        session["credits"] -= 1
        session.modified = True

        return jsonify({

            "answer": answer,

            "credits":
                session["credits"]

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

    return """
    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

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

            <div class="logo">
                G
            </div>

            <h1>
                Upgrade Garona AI
            </h1>

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