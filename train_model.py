import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import joblib

# Sample dataset
data = {
    "text": [
        "hello world",
        "login successful",
        "view account details",
        "transfer money",
        "' OR 1=1 --",
        "<script>alert(1)</script>",
        "DROP TABLE users;",
        "SELECT * FROM users WHERE id=1",
        "' OR 'a'='a",
        "<img src=x onerror=alert(1)>"
    ],
    "label": [
        0, 0, 0, 0,   # Normal
        1, 1, 1, 1, 1, 1  # Malicious
    ]
}

df = pd.DataFrame(data)

# Convert text into numbers
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(df["text"])
y = df["label"]

# Train model
model = LogisticRegression()
model.fit(X, y)

# Save model and vectorizer
joblib.dump(model, "model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("Model trained and saved successfully!")
