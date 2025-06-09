import os
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from openai import OpenAI
import google.generativeai as genai
from langdetect import detect

# --- API Key Configuration ---
# It's recommended to use a more secure way to manage the app's secret key in production
app.secret_key = os.urandom(24) 

# --- Client Initialization ---
# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure and initialize Google Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
# Allow credentials to handle session cookies
CORS(app, supports_credentials=True)

# --- Prompts and Constants ---
# System prompt that enforces topic and tagging for both models
SYSTEM_PROMPT_CONTENT = (
    "You are a helpful assistant that ONLY strict instructions answers questions related to Bad Lippspringe, Germany — "
    "including local services, events, weather, transportation, and local history.\n"
    "If a user asks something unrelated (e.g., about another city of Germany or Deutschland), DO NOT answer.\n"
    "You must always follow these strict instructions: ✅ VERIFIED INFORMATION ONLY\n"
    "Only provide information that has been explicitly verified to be accurate and current.\n"
    "Never guess, assume, or infer any detail — if something cannot be confirmed, say so clearly.\n"
    "Instead, respond ONLY with the special tag: __OUT_OF_SCOPE__ on its own line, and stop.\n"
    "You must not explain or reply to out-of-scope questions. Just output the tag and nothing more."
)

# Fallback messages per language
FALLBACK_MESSAGES = {
    "en": "I'm really sorry, but I'm designed to assist only with information about Bad Lippspringe. Could you please check your question and ask again about something related to Bad Lippspringe? I'd be happy to help you!",
    "de": "Es tut mir leid, aber ich bin darauf spezialisiert, nur Informationen über Bad Lippspringe bereitzustellen. Könntest du bitte deine Frage überprüfen und erneut etwas zu Bad Lippspringe fragen? Ich helfe dir gerne weiter!",
    "pt": "Desculpe, mas fui projetado para fornecer informações apenas sobre Bad Lippspringe. Poderia verificar sua pergunta e perguntar novamente algo relacionado a Bad Lippspringe? Ficarei feliz em ajudar!",
    "es": "Lo siento mucho, pero estoy diseñado para proporcionar información solo sobre Bad Lippspringe. ¿Podrías revisar tu pregunta y volver a preguntar algo relacionado con Bad Lippspringe? ¡Estaré encantado de ayudarte!",
    "tr": "Üzgünüm, ancak yalnızca Bad Lippspringe hakkında bilgi sağlamak üzere tasarlandım. Lütfen sorunuzu kontrol edip Bad Lippspringe ile ilgili bir şey sorar mısınız? Size yardımcı olmaktan memnuniyet duyarım!",
}
DEFAULT_LANGUAGE = "en"

# --- Route Definitions ---
@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return '', 204

    data = request.json
    user_input = data.get("message", "").strip()
    model_choice = data.get("model", "chatgpt").strip().lower()

    if not user_input:
        return jsonify({"response": "Please enter a message."})

    # Detect language for fallback messages
    try:
        detected_lang = detect(user_input)
    except:
        detected_lang = DEFAULT_LANGUAGE

    # Get or initialize conversation history from the session
    if 'history' not in session or not isinstance(session['history'], dict):
        session['history'] = {'chatgpt': [], 'gemini': []}
        
    # Append user message to the correct history
    session['history'][model_choice].append({"role": "user", "content": user_input})
    session.modified = True
    
    try:
        if model_choice == "gemini":
            if not GEMINI_API_KEY:
                 return jsonify({"response": "Gemini API key is not configured."}), 500
            
            model = genai.GenerativeModel('gemini-pro')
            # Format history for Gemini
            gemini_history = [
                {"role": "user", "parts": [SYSTEM_PROMPT_CONTENT]},
                {"role": "model", "parts": ["Understood. I will only answer questions about Bad Lippspringe."]}
            ] + [{"role": entry["role"], "parts": [entry["content"]]} for entry in session['history']['gemini']]

            response = model.generate_content(gemini_history)
            reply = response.text.strip()

        else: # Default to ChatGPT
            if not openai_client.api_key:
                 return jsonify({"response": "OpenAI API key is not configured."}), 500
                 
            # Format history for OpenAI
            chatgpt_history = [{"role": "system", "content": SYSTEM_PROMPT_CONTENT}] + session['history']['chatgpt']

            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=chatgpt_history,
                max_tokens=1000,
                temperature=0.7
            )
            reply = response.choices[0].message.content.strip()

        # Handle out-of-scope responses
        if "__OUT_OF_SCOPE__" in reply:
            localized_msg = FALLBACK_MESSAGES.get(detected_lang[:2], FALLBACK_MESSAGES[DEFAULT_LANGUAGE])
            return jsonify({"response": localized_msg})

        # Append assistant response to the correct history
        session['history'][model_choice].append({"role": "assistant", "content": reply})
        session.modified = True

        return jsonify({"response": reply})

    except Exception as e:
        # Log the full error for debugging
        print(f"An error occurred with model {model_choice}: {str(e)}")
        return jsonify({"response": f"An error occurred while processing your request. Please try again later."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
