from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # USERS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    # CHAT TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chats(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        message TEXT,
        reply TEXT
    )
    """)

    # FAQ TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS faq(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT
    )
    """)

    # INSERT DEFAULT FAQ (ONLY ONCE)
    cur.execute("SELECT COUNT(*) FROM faq")
    count = cur.fetchone()[0]

    if count == 0:
        faqs = [
            ("course,bca,mca", "We offer BCA, MCA, BBA and more courses."),
            ("fees,price,cost", "Fees range between ₹50,000 - ₹1,00,000 per year."),
            ("admission,apply", "Admissions are open! You can apply online."),
            ("placement,job", "We provide placement support with top companies."),
            ("hostel", "Hostel facility is available for students.")
        ]

        for q, a in faqs:
            cur.execute("INSERT INTO faq(question, answer) VALUES (?, ?)", (q, a))

    conn.commit()
    conn.close()

init_db()

# ---------------- CHATBOT (FAQ BASED) ----------------
def chatbot_reply(msg):
    msg = msg.lower()

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT question, answer FROM faq")
    faqs = cur.fetchall()
    conn.close()

    best_match = None

    for question, answer in faqs:
        keywords = question.split(",")

        for word in keywords:
            if word.strip() in msg:
                return answer

    return "Sorry, I didn’t understand. Please ask about courses, fees, admission, or placement."

# ---------------- ROUTES ----------------

# Landing Page
@app.route("/")
def landing():
    return render_template("landing.html")

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn = sqlite3.connect("users.db")
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO users(name,email,password) VALUES(?,?,?)",
                (name, email, password)
            )

            conn.commit()
            conn.close()

            return redirect("/login")

        except:
            error = "User already exists"

    return render_template("register.html", error=error)

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT name FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = email
            session["user_name"] = user[0]
            return redirect("/chat")
        else:
            error = "Invalid email or password"

    return render_template("login.html", error=error)

# Chat Page
@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/login")

    return render_template("chat.html", name=session.get("user_name"))

# Start Chat Button Flow
@app.route("/start-chat")
def start_chat():
    if "user" in session:
        return redirect("/chat")
    return redirect("/login")

# Chat Response
@app.route("/get", methods=["POST"])
def get_response():
    if "user" not in session:
        return jsonify({"reply": "Please login first."})

    data = request.get_json()
    msg = data.get("message")

    reply = chatbot_reply(msg)

    # Save chat
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chats(user, message, reply) VALUES (?, ?, ?)",
        (session["user"], msg, reply)
    )
    conn.commit()
    conn.close()

    return jsonify({"reply": reply})

# ---------------- ADMIN PANEL ----------------

@app.route("/admin", methods=["GET", "POST"])
def admin():
    # simple admin check
    if session.get("user") != "admin@gmail.com":
        return "Access Denied"

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    if request.method == "POST":
        question = request.form["question"]
        answer = request.form["answer"]

        cur.execute(
            "INSERT INTO faq(question, answer) VALUES (?, ?)",
            (question, answer)
        )
        conn.commit()

    cur.execute("SELECT * FROM faq")
    faqs = cur.fetchall()
    conn.close()

    return render_template("admin.html", faqs=faqs)

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run()