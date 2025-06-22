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
SYSTEM_PROMPT = (  "You are "Bad Lippspringe Guide," a specialized and highly precise city guide for Bad Lippspringe, Germany. Your sole task is to provide tourists and visitors with fact-based and correct information about Bad Lippspringe."         
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
