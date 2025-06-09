import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import google.generativeai as genai
from langdetect import detect

# --- Client Initialization ---
# Initialize OpenAI client
# Your key should be set as an environment variable: OPENAI_API_KEY
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure and initialize Google Gemini client
# Your key should be set as an environment variable: GEMINI_API_KEY
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
# Enable Cross-Origin Resource Sharing
CORS(app)

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
    alert("This is an alert message!"+model_choice);

    if not user_input:
        return jsonify({"response": "Please enter a message."})

    # Detect language for fallback messages
    try:
        detected_lang = detect(user_input)
    except:
        detected_lang = DEFAULT_LANGUAGE

    try:
        reply = ""
        if model_choice == "gemini":
            if not GEMINI_API_KEY:
                 return jsonify({"response": "Gemini API key is not configured on the server."}), 500
            
            model = genai.GenerativeModel('gemini-pro')
            # For a stateless call, we combine the system prompt and user input
            full_prompt = f"{SYSTEM_PROMPT_CONTENT}\n\nUser Question: {user_input}"
            response = model.generate_content(full_prompt)
            reply = response.text.strip()

        else: # Default to ChatGPT
            if not openai_client.api_key:
                 return jsonify({"response": "OpenAI API key is not configured on the server."}), 500
                 
            # For a stateless call, the message list contains the system role and the user role
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_CONTENT},
                {"role": "user", "content": user_input}
            ]

            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            reply = response.choices[0].message.content.strip()

        # Handle out-of-scope responses
        if "__OUT_OF_SCOPE__" in reply:
            localized_msg = FALLBACK_MESSAGES.get(detected_lang[:2], FALLBACK_MESSAGES[DEFAULT_LANGUAGE])
            return jsonify({"response": localized_msg})

        return jsonify({"response": reply})

    except Exception as e:
        # Log the full error for debugging on the server
        print(f"An error occurred with model '{model_choice}': {str(e)}")
        # Return a generic error message to the user
        return jsonify({"response": "An error occurred while processing your request. Please try again later."}), 500

if __name__ == "__main__":
    # The development server will run on http://localhost:5000
    app.run(host="0.0.0.0", port=5000)
