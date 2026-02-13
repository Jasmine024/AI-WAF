from flask import Flask, render_template, request, send_file
import joblib
import csv
from datetime import datetime
import os

app = Flask(__name__)

# Load ML model
model = joblib.load("model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

LOG_FILE = "attack_logs.csv"


@app.route("/", methods=["GET", "POST"])
def home():
    prediction = None

    if request.method == "POST":
        user_input = request.form["user_input"]

        # ML Processing
        input_vector = vectorizer.transform([user_input])
        result = model.predict(input_vector)[0]
        probability = model.predict_proba(input_vector)[0]
        confidence = round(max(probability) * 100, 2)

        if result == 1:
            label = "Malicious"
            prediction = f"⚠ Malicious Input Detected! (Confidence: {confidence}%)"
        else:
            label = "Normal"
            prediction = f"✅ Normal Input (Confidence: {confidence}%)"

        # Logging
        with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            if file.tell() == 0:
                writer.writerow(["Timestamp", "Input", "Type", "Confidence"])

            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                user_input,
                label,
                f"{confidence}%"
            ])

    return render_template("index.html", prediction=prediction)


@app.route("/dashboard")
def dashboard():
    logs = []
    total_requests = 0
    total_attacks = 0
    attack_rate = 0

    if os.path.isfile(LOG_FILE):
        with open(LOG_FILE, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)
            logs = list(reader)

        total_requests = len(logs)
        total_attacks = sum(1 for row in logs if row[2] == "Malicious")

        if total_requests > 0:
            attack_rate = round((total_attacks / total_requests) * 100, 2)

    last_10 = logs[-10:][::-1]

    return render_template(
        "dashboard.html",
        total_requests=total_requests,
        total_attacks=total_attacks,
        attack_rate=attack_rate,
        last_10=last_10
    )


@app.route("/download_logs")
def download_logs():
    if os.path.isfile(LOG_FILE):
        return send_file(LOG_FILE, as_attachment=True)
    return "No logs available"


if __name__ == "__main__":
    app.run()
