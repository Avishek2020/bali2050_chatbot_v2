from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from langdetect import detect
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app, supports_credentials=True)

# System prompt that enforces topic and tagging
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a helpful assistant that ONLY strict instructions answers questions related to Bad Lippspringe, Germany — "
        "including local services, events, weather, transportation, and local history.\n"
        "If a user asks something unrelated (e.g., about another city of Germany or Deutschland), DO NOT answer.\n"
        "You must always follow these strict instructions: ✅ VERIFIED INFORMATION ONLY\n"
        "Only provide information that has been explicitly verified to be accurate and current.\n"
        "Never guess, assume, or infer any detail — if something cannot be confirmed, say so clearly.\n"
        "Instead, respond ONLY with the special tag: __OUT_OF_SCOPE__ on its own line, and stop.\n"
        "You must not explain or reply to out-of-scope questions. Just output the tag and nothing more."
    )
}

# Fallback messages per language
FALLBACK_MESSAGES = {
    "en": "I'm really sorry, but I'm designed to assist only with information about Bad Lippspringe. Could you please check your question and ask again about something related to Bad Lippspringe? I'd be happy to help you!",
    "de": "Es tut mir leid, aber ich bin darauf spezialisiert, nur Informationen über Bad Lippspringe bereitzustellen. Könntest du bitte deine Frage überprüfen und erneut etwas zu Bad Lippspringe fragen? Ich helfe dir gerne weiter!",
    "pt": "Desculpe, mas fui projetado para fornecer informações apenas sobre Bad Lippspringe. Poderia verificar sua pergunta e perguntar novamente algo relacionado a Bad Lippspringe? Ficarei feliz em ajudar!",
    "es": "Lo siento mucho, pero estoy diseñado para proporcionar información solo sobre Bad Lippspringe. ¿Podrías revisar tu pregunta y volver a preguntar algo relacionado con Bad Lippspringe? ¡Estaré encantado de ayudarte!",
    "tr": "Üzgünüm, ancak yalnızca Bad Lippspringe hakkında bilgi sağlamak üzere tasarlandım. Lütfen sorunuzu kontrol edip Bad Lippspringe ile ilgili bir şey sorar mısınız? Size yardımcı olmaktan memnuniyet duyarım!",
}
DEFAULT_LANGUAGE = "en"

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return '', 204

    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"response": "Please enter a message."})

    # Detect language
    try:
        detected_lang = detect(user_input)
    except:
        detected_lang = DEFAULT_LANGUAGE

    # Setup session history
    if "history" not in session:
        session["history"] = [SYSTEM_PROMPT]

    session["history"].append({"role": "user", "content": user_input})

    try:
        # Query OpenAI with latest model gpt-4o
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=session["history"],
            max_tokens=1000,
            temperature=0.7
        )
        reply = response.choices[0].message['content'].strip()

        if "__OUT_OF_SCOPE__" in reply:
            localized_msg = FALLBACK_MESSAGES.get(detected_lang[:2], FALLBACK_MESSAGES[DEFAULT_LANGUAGE])
            return jsonify({"response": localized_msg})

        session["history"].append({"role": "assistant", "content": reply})
        session.modified = True

        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"response": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
