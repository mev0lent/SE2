import os
from flask import Flask, request, render_template, jsonify
from openai import OpenAI
from cryptography.fernet import Fernet

# Load the encryption key
with open("encryption_key.key", "rb") as key_file:
    encryption_key = key_file.read()

cipher = Fernet(encryption_key)

# Decrypt the API key
with open("encrypted_api_key.txt", "rb") as encrypted_file:
    encrypted_key = encrypted_file.read()
api_key = cipher.decrypt(encrypted_key).decode()

client = OpenAI(api_key=api_key)
app = Flask(__name__)

# Function to get analysis from OpenAI
def analyze_feedback(feedback):
    messages = [
        {
            "role": "user",
            "content": (
                "Bitte kategorisiere das Feedback von Studierenden in eine der folgenden Kategorien: "
                "a) Lehrmaterialien, b) Unterricht, c) Inhaltliches. "
                "Zusammengefasste Version des Feedbacks angeben. "
                "Zusätzlich eine Sentiment-Analyse durchführen und in Stichworten beschreiben. "
                f"Feedback: {feedback}"
            )
        }
    ]
    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message.content

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    feedback = data.get('feedback', '')
    analysis_result = analyze_feedback(feedback)

    # Parsing the response
    category = None
    sentiment = None
    summarized_feedback = None

    if analysis_result:
        lines = analysis_result.split('\n')
        for line in lines:
            if line.startswith("Kategorie:"):
                category = line.split(":", 1)[1].strip()
            elif line.startswith("Feedback:"):
                summarized_feedback = line.split(":", 1)[1].strip()
            elif line.startswith("Sentiment:"):
                sentiment = line.split(":", 1)[1].strip()
    print("OpenAI response:", analysis_result)

    return jsonify({
        "category": category,
        "summarized_feedback": summarized_feedback,
        "sentiment": sentiment
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
