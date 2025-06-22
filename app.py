from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
import os

# Initialize Gemini Client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Updated System Prompt without __OUT_OF_SCOPE__ and with verified URLs
SYSTEM_PROMPT = (
    "You are a helpful assistant who provides accurate, current, and verified information about Bad Lippspringe, Germany. "
    "You may include local services, events, transportation, weather, healthcare, history, and culture.\n\n"
    "Use ONLY the following sources to inform your answers when relevant:\n"
    "- https://www.bad-lippspringe.de\n"
    "- https://www.vitalpina.de\n"
    "- https://www.teutoburgerwald.de\n"
    "- https://www.kurpark-badlippspringe.de\n"
    "- https://de.wikipedia.org/wiki/Bad_Lippspringe\n\n"
    "Never hallucinate or invent facts not found or inferable from the above sources.\n\n"
    "Formatting rules:\n"
    "- Do NOT use markdown formatting (no bold, italic, headers, or bullet symbols).\n"
    "- Use plain text only. Write clear, clean sentences.\n"
    "- Structure responses using clear section titles like 'Sports', 'Culture', 'Healthcare' — but without styling.\n\n"
    "Example:\n"
    "Sports:\nHiking trails are available in the Teutoburg Forest starting near Kurwald Park.\n"
    "Culture:\nArminiuspark offers concerts and seasonal festivals throughout the year.\n"
)

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return '', 204

    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"response": "Please enter a message."})

    try:
        # Send chat session to Gemini with updated system prompt
        chat = model.start_chat(history=[
            {"role": "system", "parts": [SYSTEM_PROMPT]},
            {"role": "user", "parts": [user_input]}
        ])

        response = chat.send_message(user_input)
        reply = response.text.strip()

        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"response": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
