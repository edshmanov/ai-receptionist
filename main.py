from flask import Flask, request
import requests
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return "ok", 200
    
    message = data.get("message", {})
    event_type = message.get("type", "")
    
    if event_type != "end-of-call-report":
        return "ok", 200
    
    transcript = message.get("transcript", "No transcript")
    caller = message.get("customer", {}).get("number", "Unknown")
    duration = round(message.get("durationSeconds", 0))
    
    text = f"📞 New Lead!\n\nPhone: {caller}\nDuration: {duration} sec\n\nConversation:\n{transcript}"
    
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text}
    )
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
