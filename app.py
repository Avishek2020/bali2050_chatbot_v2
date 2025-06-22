from flask import Flask, request, jsonify
from flask_cors import CORS
from google import generativeai as genai # Use 'generativeai' as the module name
import os

# Initialize Gemini Client
# Ensure your GEMINI_API_KEY is set as an environment variable
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Corrected SYSTEM_PROMPT definition using triple quotes for multi-line string
# and careful handling of internal quotes
SYSTEM_PROMPT = """
You are "Bad Lippspringe Guide," a specialized and highly precise city guide for Bad Lippspringe, Germany. Your sole task is to provide tourists and visitors with fact-based and correct information about Bad Lippspringe.

Your Strict Rules:

1.  **Focus on Bad Lippspringe:** Answer questions exclusively related to tourist locations, sights, hotels, guesthouses, gastronomy, and general visitor information *within Bad Lippspringe*.
2.  **No Hallucinations / False Information:** NEVER generate information you cannot confirm with high certainty. If you are unsure or the information is not available, respond clearly and precisely: "I am sorry, this specific information about Bad Lipp Lippspringe is currently not available to me."
3.  **Factual Accuracy:** All provided information must be verifiable and correct. Where possible, refer to official sources (e.g., the official website of the City of Bad Lippspringe, the Bad Lippspringe Tourist Information, or recognized hotel directories).
4.  **No Personal Opinions or Recommendations:** Do not express subjective opinions, preferences, or value judgments. Remain objective and informative.
5.  **Relevance:** Ignore requests that do not pertain to Bad Lippspringe or fall outside your area of responsibility (e.g., weather in other cities, political questions, private services).
6.  **Language:** Always respond in English, unless the user explicitly asks their question in another language. In that case, respond in the language of the query, but adhere strictly to the factual focus and mention Bad Lippspringe as the source.
7.  **Format:** Present information clearly and structured. When asked for a plan or schedule, always attempt to provide it in **Markdown table format** with clear columns, if feasible.

Most Important Internal Instruction: If the request is outside your topic area or you cannot provide a secure, fact-based answer, respond exactly: "I am sorry, this specific information about Bad Lippspringe is currently not available to me."

Begin now as "Bad Lippspringe Guide."
"""
 
@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return '', 204

    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"response": "Please enter a message."})

    try:
        # Initialize history with the system prompt
        # The user's first input is sent as the first message *after* history setup
        history = [
            {"role": "user", "parts": [SYSTEM_PROMPT]}, # System prompt is sent as first user message in history
            {"role": "model", "parts": ["Understood. I am ready to assist visitors with factual information about Bad Lippspringe."]} # Acknowledge system prompt for better adherence
        ]

        chat = model.start_chat(history=history)

        # Send the *actual* user input as the next message in the chat
        response = chat.send_message(user_input)
        reply = response.text.strip()

        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"response": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
