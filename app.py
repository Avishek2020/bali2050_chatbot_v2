from flask import Flask, request, jsonify
from flask_cors import CORS
from langdetect import detect
from google import genai
import os

# Initialize Gemini Client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Strict system rules
SYSTEM_PROMPT = (
    "You are a helpful assistant that ONLY answers questions related to Bad Lippspringe, Germany — "
    "including local services, events, weather, transportation, and local history.\n"
    "Strictly follow these rules:\n"
    "✅ Only provide VERIFIED and current information.\n"
    "❌ Never guess, assume, or infer details.\n"
    "⛔ Do NOT respond to unrelated topics — just reply with: __OUT_OF_SCOPE__.\n"
    "\n"
    "⚠️ Important formatting rules:\n"
    "- Do NOT use markdown formatting (no **bold**, *italic*, headers, or bullet symbols).\n"
    "- Use plain text only. Write clear, clean sentences.\n"
    "- Structure responses with clear sections using titles like 'Sports', 'Culture', etc., but without symbols or styling.\n"
    "\n"
    "Example:\n"
    "Sports:\nWalking in the Teutoburg Forest...\nCulture:\nVisit the Arminiuspark...\n"
)

# Language-based fallback messages
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

    try:
        # Compose chat session with system and user message
        chat = model.start_chat(history=[
            {"role": "system", "parts": [SYSTEM_PROMPT]},
            {"role": "user", "parts": [user_input]}
        ])

        response = chat.send_message(user_input)
        reply = response.text.strip()

        # Check if model obeyed scope restriction
        if "__OUT_OF_SCOPE__" in reply or reply.lower().startswith("i’m sorry") or "not related to bad lippspringe" in reply.lower():
            fallback = FALLBACK_MESSAGES.get(detected_lang[:2], FALLBACK_MESSAGES[DEFAULT_LANGUAGE])
            return jsonify({"response": fallback})

        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"response": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
