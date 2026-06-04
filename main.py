from flask import Flask, request
import requests
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


def extract_info(transcript):
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-haiku-4-5",
            "max_tokens": 300,
            "messages": [{
                "role": "user",
                "content": (
                    "Extract info from this call transcript.\n"
                    "Return ONLY this JSON format, no markdown, no explanation:\n"
                    "{\"name\":\"value\",\"address\":\"value\",\"service\":\"value\",\"time\":\"value\"}\n\n"
                    "Use 'Not provided' if info is missing.\n\n"
                    "Transcript:\n" + transcript
                )
            }]
        },
        timeout=15
    )
    import json
    raw = resp.json()["content"][0]["text"].strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return "ok", 200
    msg = data.get("message", {})
    if msg.get("type") != "end-of-call-report":
        return "ok", 200
    transcript = msg.get("transcript", "")
    caller = msg.get("customer", {}).get("number", "Unknown")
    try:
        info = extract_info(transcript)
    except Exception as e:
        info = {"name": "?", "address": "?", "service": "?", "time": "?"}
    text = (
        f"📞 New Lead!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 Name: {info.get('name','?')}\n"
        f"📱 Phone: {caller}\n"
        f"📍 Address: {info.get('address','?')}\n"
        f"🔧 Service: {info.get('service','?')}\n"
        f"📅 Time: {info.get('time','?')}\n"
        f"━━━━━━━━━━━━━━━"
    )
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text}
    )
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
