import os
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
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

# Initialize Flask app and enable CORS
app = Flask("StudyVoice")
CORS(app)

# Function to get analysis from OpenAI
def analyze_feedback(feedback):
    messages = [
        {
            "role": "user",
            "content": (
                "Bitte analysiere das Feedback eines Studierenden und liefere die Antwort IMMER strikt im folgenden Format:\n"
                "Zeile 1: **Kategorie:** [eine der folgenden Optionen: Lehrmaterialien, Unterricht, Inhaltliches]\n"
                "Zeile 2: **Zusammenfassung:** [kurze Zusammenfassung des Feedbacks in maximal zwei Sätzen]\n"
                "Zeile 3: **Stimmung:** [Sentiment-Analyse in maximal fünf Stichpunkten, z. B. - Positiv, - Begeisterung]\n\n"
                f"Hier ist das Feedback, das analysiert werden soll:\n{feedback}"
            )
        }
    ]
    try:
        print("Sending to OpenAI:", messages)  # Debugging: Zeige gesendete Anfrage
        response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        print("OpenAI Response:", response)  # Debugging: Zeige API-Antwort
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in OpenAI API call: {e}")
        return None


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        feedback = data.get('feedback', '')
        if not feedback:
            return jsonify({"error": "No feedback provided"}), 400

        analysis_result = analyze_feedback(feedback)
        if not analysis_result:
            return jsonify({"error": "Failed to analyze feedback"}), 500

        # Initialize variables
        category = "N/A"
        summarized_feedback = "N/A"
        sentiment = "N/A"

        # Parse the OpenAI response
        try:
            lines = [line.strip() for line in analysis_result.split('\n') if line.strip()]  # Entferne leere Zeilen
            for i, line in enumerate(lines):
                if line.startswith("**Kategorie:**"):
                    # Alles nach "**Kategorie:**" extrahieren
                    category = line.split("**Kategorie:**", 1)[1].strip()
                elif line.startswith("**Zusammenfassung:**"):
                    # Alles nach "**Zusammenfassung:**" extrahieren
                    summarized_feedback = line.split("**Zusammenfassung:**", 1)[1].strip()
                elif line.startswith("**Stimmung:**"):
                    # Alles nach "**Stimmung:**" und die folgenden Zeilen extrahieren
                    sentiment_parts = line.split("**Stimmung:**", 1)[1].strip()
                    following_lines = lines[i + 1:]  # Alle folgenden Zeilen
                    all_sentiment_lines = [sentiment_parts] + following_lines  # Kombiniere alles
                    sentiment = "\n".join([line for line in all_sentiment_lines if line.strip()])  # Entferne leere Zeilen
        except Exception as e:
            print(f"Error parsing OpenAI response: {e}")
            return jsonify({"error": "Parsing error: Response format invalid"}), 500

        # Return the parsed response
        return jsonify({
            "category": category if category != "N/A" else "Keine Kategorie erkannt",
            "summarized_feedback": summarized_feedback if summarized_feedback != "N/A" else "Keine Zusammenfassung verfügbar",
            "sentiment": sentiment if sentiment.strip() else "Keine Stimmungsanalyse verfügbar"
        })
    except Exception as e:
        print(f"Error in analysis endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
