from flask import Flask, request, jsonify, session
from flask_cors import CORS
from langdetect import detect
import google.generativeai as genai
import os

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro")

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.getenv("FLASK_SECRET", "your-secret-key")  # Needed for session

# System prompt
SYSTEM_PROMPT = (
    "You are a helpful assistant that ONLY strict instructions answers questions related to Bad Lippspringe, Germany — "
    "including local services, events, weather, transportation, and local history.\n"
    "If a user asks something unrelated (e.g., about another city of Germany or Deutschland), DO NOT answer.\n"
    "You must always follow these strict instructions: ✅ VERIFIED INFORMATION ONLY\n"
    "Only provide information that has been explicitly verified to be accurate and current.\n"
    "Never guess, assume, or infer any detail — if something cannot be confirmed, say so clearly.\n"
    "Instead, respond ONLY with the special tag: __OUT_OF_SCOPE__ on its own line, and stop.\n"
    "You must not explain or reply to out-of-scope questions. Just output the tag and nothing more."
)

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

    # Maintain session-based history
    if "history" not in session:
        session["history"] = [{"role": "user", "parts": [SYSTEM_PROMPT]}]

    session["history"].append({"role": "user", "parts": [user_input]})

    try:
        chat_response = model.generate_content(session["history"])
        reply = chat_response.text.strip()

        if "__OUT_OF_SCOPE__" in reply:
            fallback = FALLBACK_MESSAGES.get(detected_lang[:2], FALLBACK_MESSAGES[DEFAULT_LANGUAGE])
            return jsonify({"response": fallback})

        session["history"].append({"role": "model", "parts": [reply]})
        session.modified = True

        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"response": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
