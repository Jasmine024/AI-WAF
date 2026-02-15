from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import pickle
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- LOAD ML MODEL ---------------- #

model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# ---------------- DATABASE SETUP ---------------- #

def init_db():
    conn = sqlite3.connect("waf.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ip_address TEXT,
            input_text TEXT,
            attack_type TEXT,
            confidence REAL,
            severity TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ---------------- #

USERNAME = "admin"
PASSWORD = "admin123"

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["user"] = USERNAME
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid Credentials")
    return render_template("login.html")

# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("waf.db")
    c = conn.cursor()

    c.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 10")
    logs = c.fetchall()

    c.execute("SELECT COUNT(*) FROM logs")
    total_requests = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM logs WHERE attack_type!='NORMAL'")
    total_attacks = c.fetchone()[0]

    attack_rate = 0
    if total_requests > 0:
        attack_rate = round((total_attacks / total_requests) * 100, 2)

    # 🔴 HIGH ALERT CHECK
    high_alert = False
    if logs:
        if logs[0][6] in ["HIGH", "CRITICAL"]:
            high_alert = True

    conn.close()

    return render_template(
        "dashboard.html",
        logs=logs,
        total_requests=total_requests,
        total_attacks=total_attacks,
        attack_rate=attack_rate,
        high_alert=high_alert
    )

# ---------------- PREDICT ---------------- #

@app.route("/predict", methods=["POST"])
def predict():
    if "user" not in session:
        return redirect(url_for("login"))

    input_text = request.form["input"]
    ip_address = request.remote_addr

    # ML Prediction
    vector = vectorizer.transform([input_text])
    raw_prediction = model.predict(vector)[0]

    # OPTIONAL: if model supports probability
    try:
        prob = model.predict_proba(vector)[0]
        confidence = round(max(prob) * 100, 2)
    except:
        confidence = 85.0

    # ---------------- MULTI-CLASS READY ---------------- #

    attack_labels = {
        0: "NORMAL",
        1: "SQL Injection",
        2: "XSS",
        3: "Command Injection",
        4: "Path Traversal"
    }

    prediction = attack_labels.get(raw_prediction, "ATTACK")

    # ---------------- SEVERITY LOGIC ---------------- #

    if prediction == "NORMAL":
        severity = "LOW"
    elif prediction in ["SQL Injection", "XSS"]:
        severity = "HIGH"
    else:
        severity = "CRITICAL"

    # ---------------- SAVE TO DATABASE ---------------- #

    conn = sqlite3.connect("waf.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO logs (timestamp, ip_address, input_text, attack_type, confidence, severity)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ip_address,
        input_text,
        prediction,
        confidence,
        severity
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))

# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- RUN SERVER ---------------- #

if __name__ == "__main__":
    app.run(debug=True, port=10000)
