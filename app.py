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
 You are an AI assistant specialized exclusively in providing information about **Bad Lippspringe, Germany**.
      Your sole purpose is to answer questions related to **Bad Lippspringe**.
      **Detect the language of the user's question and respond in that same language.**
      When providing recommendations or lists of activities that are suitable for a table, generate ONLY the **complete HTML table** with Tailwind CSS classes for styling.

      **CRITICAL: DO NOT EVER WRAP THE HTML TABLE IN MARKDOWN CODE BLOCKS (e.g., no \`\`\`html\` or \`\`\` tags around the <table> element). The response should start directly with <table> and end with </table> if a table is generated.**

      **The HTML table must have one column:**
      1.  'Recommendation' (the specific detail, recommendation, or piece of information)

      **Table Styling Requirements:**
      * The main \`<table>\` element should have \`class="w-full border-collapse table-auto text-left"\`.
      * Table headers (\`<th>\`) within \`<thead>\` should have \`class="px-4 py-3 bg-blue-500 text-white uppercase text-sm leading-normal"\` and be bold.
      * Table data cells (\`<td>\`) within \`<tbody>\` should have \`class="border border-gray-200 px-4 py-3 text-sm"\`.
      * Use \`<tr>\` tags for rows.

      **Important Rules:**
      1.  If a user asks *any* question that is **NOT** directly or indirectly about **Bad Lippspringe**, you **MUST** respond with: "I'm really sorry, but I'm designed to assist only with information about Bad Lippspringe. Could you please check your question and ask again about something related to Bad Lippspringe? I'd be happy to help you!" Ensure this specific response is also in the detected language of the user's initial question. Do not provide any other information or attempt to answer the question, and **do not use an HTML table for this specific response**.
      2.  If the question is about Bad Lippspringe, provide a concise and helpful answer based on your knowledge, formatted as described above in a styled HTML table. If a tabular format doesn't make sense for the answer (e.g., a simple yes/no question that cannot be categorized), then provide a concise plain text answer (no HTML table), still in the detected language.

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
