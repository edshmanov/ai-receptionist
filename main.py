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

        caller = msg.get("customer", {}).get("number", "Unknown")
        summary = msg.get("summary", "")

        # Extract from summary using simple search
        import re
        name = re.search(r'([A-Z][a-z]+ [A-Z][a-z]+) called', summary)
        phone = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', summary)
        address = re.search(r'(\d+\s[\w\s]+(?:North|South|East|West|St|Ave|Rd|Blvd|Dr|Ln)[^\)\.]+)', summary)
        time = re.search(r'(tomorrow[^\.]+|(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[^\.]+\d+\s*(?:AM|PM))', summary, re.I)
        service = re.search(r'(plumb|pipe|leak|roof|electr|handyman|repair|hvac|drain)[^\.\,]{0,60}', summary, re.I)

        text = (
            f"📞 New Lead!\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 Name: {name.group(1) if name else 'Unknown'}\n"
            f"📱 Phone: {phone.group(0) if phone else caller}\n"
            f"📍 Address: {address.group(1).strip() if address else 'Not provided'}\n"
            f"🔧 Service: {service.group(0).strip() if service else 'Not provided'}\n"
            f"📅 Time: {time.group(1).strip() if time else 'Not provided'}\n"
            f"━━━━━━━━━━━━━━━"
        )

        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text}
        )
    except Exception as e:
        print(f"Error: {e}")
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
