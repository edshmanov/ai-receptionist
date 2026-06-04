from flask import Flask, request
import requests
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        if not data:
            return "ok", 200
        msg = data.get("message", {})
        if msg.get("type") != "end-of-call-report":
            return "ok", 200
        transcript = msg.get("transcript", "No transcript")
        caller = msg.get("customer", {}).get("number", "Unknown")
        summary = msg.get("summary", "")
        text = (
            f"📞 New Lead!\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📱 Phone: {caller}\n\n"
            f"📋 Summary:\n{summary}\n\n"
            f"📝 Full transcript:\n{transcript}\n"
            f"━━━━━━━━━━━━━━━"
        )
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text[:4000]}
        )
    except Exception as e:
        print(f"Error: {e}")
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
