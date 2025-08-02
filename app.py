import os
from dotenv import load_dotenv

load_dotenv()  # Load .env into environment


from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai
import requests
from pydub import AudioSegment

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
def extract_intent(message):
    """Very basic fintech intent routing"""
    lowered = message.lower()
    if "balance" in lowered:
        return "balance"
    elif "send" in lowered or "transfer" in lowered:
        return "transfer"
    elif "loan" in lowered:
        return "loan"
    else:
        return "chat"

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get("Body")
    media_url = request.form.get("MediaUrl0")
    resp = MessagingResponse()
    msg = resp.message()

    if media_url:
        audio_data = requests.get(media_url).content
        with open("voice.ogg", "wb") as f:
            f.write(audio_data)
        sound = AudioSegment.from_ogg("voice.ogg")
        sound.export("voice.wav", format="wav")
        with open("voice.wav", "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            incoming_msg = transcript["text"]

    # Intent routing
    intent = extract_intent(incoming_msg)

    if intent == "balance":
        msg.body("Your current balance is UGX 234,000.")
    elif intent == "transfer":
        msg.body("To transfer funds, please reply with:
Send [amount] to [recipient name].")
    elif intent == "loan":
        msg.body("To apply for a loan, reply with the amount and purpose (e.g., 'Loan 50000 for school fees').")
    else:
        gpt_reply = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": incoming_msg}]
        )["choices"][0]["message"]["content"]
        msg.body(gpt_reply)

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
