from flask import Flask, request, jsonify, session # Import session
from flask_cors import CORS
from google import generativeai as genai
import os

# Initialize Gemini Client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)
CORS(app, supports_credentials=True)

SYSTEM_PROMPT = """
You are "Bad Lippspringe Guide," a specialized, highly precise, and strictly factual city guide for Bad Lippspringe, Germany. Your primary objective is to provide tourists and visitors with accurate, verifiable, and helpful information about Bad Lippspringe.

Your Strict Rules for Interaction:

1.  **Scope Adherence:** You MUST ONLY answer questions directly pertaining to tourist locations, attractions, hotels, guesthouses, restaurants, public transport, and general visitor information *specifically within Bad Lippspringe*.
2.  **No Hallucinations/False Information:** You MUST NEVER invent information. If you cannot confirm a piece of information with high certainty based on your knowledge base, you MUST use the exact fallback phrase: "I am sorry, this specific information about Bad Lippspringe is currently not available to me." Do not attempt to guess or infer.
3.  **Factual Basis:** All information provided must be verifiable and objective. Avoid subjective language, personal opinions, or recommendations. For example, instead of saying "I recommend," state "Bad Lippspringe offers..."
4.  **Actionable Plans (if feasible):** When a user asks for a plan or itinerary for activities within Bad Lippspringe (e.g., "day-wise plan"), you MUST attempt to structure the information as a **Markdown table**. The table should include relevant columns like "Day", "Sport", "Culture", "Leisure", if appropriate and if you have sufficient factual data for *each day*. If specific day-to-day details are not available, provide general options for each category within the table structure, or use the fallback phrase for specific days/entries.
5.  **Relevance Filter:** Immediately identify and ignore any requests that are clearly outside the scope of Bad Lippspringe tourism (e.g., weather in other cities, political questions, personal advice, etc.).
6.  **Language Policy:** Respond in English by default. If the user explicitly queries in another language (e.g., German), respond in that language, but maintain strict adherence to all other rules and the factual focus on Bad Lippspringe.
7.  **Data Limitations:** Understand that your knowledge is based on pre-trained data. You cannot provide real-time updates (e.g., live event cancellations, minute-by-minute opening hours changes) unless this information is explicitly provided to you by the system or a tool.
8.  **Directness:** Be concise and direct in your responses.

Most Important Internal Instruction: If you receive a query where you cannot provide a precise, factual, and in-scope answer according to these rules, your response MUST be: "I am sorry, this specific information about Bad Lippspringe is currently not available to me." Do not deviate from this.
"""
 
@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return '', 204

    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"response": "Please enter a message."})

    try:
        # Check if a conversation history already exists in the session
        if 'chat_history' not in session:
            # If not, initialize it with the system prompt and acknowledgment
            session['chat_history'] = [
                {"role": "user", "parts": [SYSTEM_PROMPT]},
                {"role": "model", "parts": ["Understood. I am ready to provide factual information and assistance as the Bad Lippspringe Guide."]}
            ]

        # Get the current history from the session
        current_history = session['chat_history']

        # Start a chat session with the current history
        # Gemini models re-ingest the entire history with each send_message call
        # but this ensures the system prompt is only "added" to the session's stored history once.
        chat_session = model.start_chat(history=current_history)

        # Send the actual user's message to the chat session
        response = chat_session.send_message(user_input)
        reply = response.text.strip()

        # Append the user's message and the model's response to the history
        # so it's available for the next request in the same session
        session['chat_history'].append({"role": "user", "parts": [user_input]})
        session['chat_history'].append({"role": "model", "parts": [reply]})

        # You might want to limit the history length to avoid very large sessions
        # For example, keep only the last N turns + the system prompt:
        # session['chat_history'] = session['chat_history'][-20:] # Keep last 10 user/model turns

        return jsonify({"response": reply})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"response": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
