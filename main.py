from flask import Flask, request
import requests
import os
import re

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

        caller = msg.get("customer", {}).get("number", "Unknown")
        summary = msg.get("summary", "")
        transcript = msg.get("transcript", "")

        # Extract name from transcript
        name = "Unknown"
        name_match = re.search(
            r"(?:my name is|i'm|i am|this is|name['s]* is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            transcript, re.I
        )
        if name_match:
            name = name_match.group(1).strip()

        # Use summary as main info
        if summary:
            text = (
                f"📞 New Lead!\n"
                f"━━━━━━━━━━━━━━━\n"
                f"👤 Name: {name}\n"
                f"📱 Phone: {caller}\n\n"
                f"📋 Summary:\n{summary}\n"
                f"━━━━━━━━━━━━━━━"
            )
        else:
            text = (
                f"📞 New Lead!\n"
                f"━━━━━━━━━━━━━━━\n"
                f"👤 Name: {name}\n"
                f"📱 Phone: {caller}\n"
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
