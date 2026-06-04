from flask import Flask, request
import requests
import os
import json

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def extract_info_with_ai(transcript):
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-haiku-4-5",
            "max_tokens": 500,
            "messages": [{
                "role": "user",
                "content": f"""Extract the following info from this call transcript and return ONLY valid JSON, nothing else:
{{
  "name": "full name or Not provided",
  "address": "full address or Not provided", 
  "service": "what service they need in one sentence",
  "appointment_time": "requested date and time or Not provided"
}}

Transcript:
{transcript}"""
            }]
        }
    )
    result = response.json()
    text = result["content"][0]["text"]
    return json.loads(text)

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

    try:
        info = extract_info_with_ai(transcript)
    except:
        info = {"name": "Unknown", "address": "Not provided", "service": "Not provided", "appointment_time": "Not provided"}

    text = (
        f"📞 New Lead!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 Name: {info.get('name')}\n"
        f"📱 Phone: {caller}\n"
        f"📍 Address: {info.get('address')}\n"
        f"🔧 Service: {info.get('service')}\n"
        f"📅 Time: {info.get('appointment_time')}\n"
        f"⏱ Duration: {duration} sec\n"
        f"━━━━━━━━━━━━━━━"
    )

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text}
    )
    return "ok", 200

if __name__
