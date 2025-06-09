from flask import Flask, request, jsonify
from flask_cors import CORS
from langdetect import detect
from google import genai
import os

# Configure Gemini client
client = genai.Client(api_key="GEMINI_API_KEY")

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Strict system prompt
SYSTEM_PROMPT = (
    "You are a helpful assistant that ONLY strict instructions answers questions related to Bad Lippspringe, Germany — "
    "including local services, events, weather, transportation, and local history.\n"
    "If a user asks something unrelated (e.g., about another city of Germany or Deutschland), DO NOT answer.\n"
)

# Fallback message by language
FALLBACK_MESSAGES = {
    "en": "I'm really sorry, but I'm designed to assist only with information about Bad Lippspringe...",
    "de": "Es tut mir leid, aber ich bin darauf spezialisiert, nur Informationen über Bad Lippspringe bereitzustellen...",
    "pt": "Desculpe, mas fui projetado para fornecer informações apenas sobre Bad Lippspringe...",
    "es": "Lo siento mucho, pero estoy diseñado para proporcionar información solo sobre Bad Lippspringe...",
    "tr": "Üzgünüm, ancak yalnızca Bad Lippspringe hakkında bilgi sağlamak üzere tasarlandım...",
}
DEFAULT_LANGUAGE = "en"

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return '', 204

    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"response": "Please enter a message."})

    try:
        detected_lang = detect(user_input)
    except:
        detected_lang = DEFAULT_LANGUAGE

    # Final prompt: system rules + user input
    full_prompt = SYSTEM_PROMPT + "\n\nUser: " + user_input

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )
        reply = response.text.strip()

        if "__OUT_OF_SCOPE__" in reply:
            fallback = FALLBACK_MESSAGES.get(detected_lang[:2], FALLBACK_MESSAGES[DEFAULT_LANGUAGE])
            return jsonify({"response": fallback})

        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"response": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
