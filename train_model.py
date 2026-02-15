import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Sample dataset
data = {
    "text": [
        "SELECT * FROM users",
        "<script>alert('XSS')</script>",
        "normal login request",
        "DROP TABLE students",
        "hello world",
        "admin OR 1=1",
        "welcome user",
        "GET /index.html"
    ],
    "label": [1, 1, 0, 1, 0, 1, 0, 0]
}

df = pd.DataFrame(data)

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df["text"])
y = df["label"]

model = LogisticRegression()
model.fit(X, y)

pickle.dump(model, open("model.pkl", "wb"))
pickle.dump(vectorizer, open("vectorizer.pkl", "wb"))

print("Model trained and saved successfully!")
