from flask import Flask, request
import requests
import os
import re

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def extract_info(transcript):
    name = "Not provided"
    phone = "Not provided"
    address = "Not provided"
    service = "Not provided"
    time = "Not provided"

    lines = transcript.split("\n")
    for i, line in enumerate(lines):
        l = line.lower()
        if "name" in l and "user:" in line.lower():
            name = line.split(":", 1)[-1].strip()
        if any(x in l for x in ["address", "zip", "street"]) and "user:" in line.lower():
            address = line.split(":", 1)[-1].strip()
        if any(x in l for x in ["tomorrow", "monday","tuesday","wednesday","thursday","friday","saturday","sunday","am","pm","morning","afternoon","evening"]) and "user:" in line.lower():
            time = line.split(":", 1)[-1].strip()
        if any(x in l for x in ["pipe","plumb","leak","roof","electric","repair","fix","install","handyman"]) and "user:" in line.lower():
            service = line.split(":", 1)[-1].strip()

    phones = re.findall(r'\+?[\d\s\-\(\)]{10,}', transcript)
    if phones:
        phone = phones[0].strip()

    return name, phone, address, service, time

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return "ok", 200

    message = data.get("message", {})
    event_type = message.get("type", "")

    if event_type != "end-of-call-report":
        return "ok", 200

    transcript = message.get("transcript", "")
    caller = message.get("customer", {}).get("number", "Unknown")
    duration = round(message.get("durationSeconds", 0))

    name, phone, address, service, appt_time = extract_info(transcript)

    text = (
        f"📞 New Lead!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 Name: {name}\n"
        f"📱 Phone: {caller}\n"
        f"📍 Address: {address}\n"
        f"🔧 Service: {service}\n"
        f"📅 Time: {appt_time}\n"
        f"⏱ Call duration: {duration} sec\n"
        f"━━━━━━━━━━━━━━━"
    )

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text}
    )
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
