from flask import Flask, request
import requests
import os
import re

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def grab(field, text):
    m = re.search(rf"{field}:\s*(.+)", text, re.I)
    if m:
        val = m.group(1).strip()
        if val and val.lower() not in ("<", "n/a", "none", "unknown", ""):
            return val
    return None

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        if not data:
            return "ok", 200

        msg = data.get("message", {})
        if msg.get("type") != "end-of-call-report":
            return "ok", 200

        caller = (
            msg.get("customer", {}).get("number") or
            msg.get("call", {}).get("customer", {}).get("number") or
            data.get("customer", {}).get("number") or
            "Unknown"
        )

        transcript = msg.get("transcript", "")
        summary = msg.get("summary", "")

        # Берём чистый блок [LEAD] из транскрипта
        lead = ""
        block = re.search(r"\[LEAD\](.+?)\[/LEAD\]", transcript, re.S | re.I)
        if block:
            lead = block.group(1)

        name = grab("Name", lead) or "Не указано"
        phone_from_lead = grab("Phone", lead)
        car = grab("Car", lead) or "Не указано"
        location = grab("Location", lead) or "Не указано"
        time_pref = grab("Time", lead) or "Не указано"
        problem = grab("Problem", lead) or (summary if summary else "Не указано")

        # Телефон: сначала из звонка, если нет — из блока
        if caller and caller != "Unknown":
            phone = caller
        elif phone_from_lead:
            phone = phone_from_lead
        else:
            phone = "Не указано"

        text = (
            f"🔧 Новая заявка — Auto House UA\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 Имя: {name}\n"
            f"📱 Телефон: {phone}\n"
            f"🚗 Авто: {car}\n"
            f"📍 Локейшн: {location}\n"
            f"📅 Время: {time_pref}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💬 Проблема: {problem}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📲 CallMind AI"
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
