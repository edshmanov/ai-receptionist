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

        # Имя
        name = "Unknown"
        name_match = re.search(
            r"(?:my name is|i'm|i am|this is|name['s]* is|меня зовут|я)\s+([A-ZА-Яa-zа-я][a-zа-я]+(?:\s+[A-ZА-Яa-zа-я][a-zа-я]+)?)",
            transcript, re.I
        )
        if name_match:
            name = name_match.group(1).strip()

        # Машина
        car = "Unknown"
        car_match = re.search(
            r"(\d{4})\s+(BMW|Toyota|Audi|Honda|Ford|Chevrolet|Mercedes|Lexus|Nissan|Hyundai|Kia|Volkswagen|VW|Subaru|Mazda|Dodge|Ram|Jeep|GMC|Cadillac|Infiniti|Acura|Volvo|Porsche|Land Rover|Range Rover|Tesla)[^\n,\.]{0,30}",
            transcript, re.I
        )
        if car_match:
            car = car_match.group(0).strip()

        # Локейшн
        location = "Not specified"
        if "arlington" in transcript.lower():
            location = "Arlington Heights"
        elif "schaumburg" in transcript.lower():
            location = "Schaumburg"

        # Время
        time_pref = "Not specified"
        time_match = re.search(
            r"(monday|tuesday|wednesday|thursday|friday|saturday|morning|afternoon|evening|tomorrow|next week|понедельник|вторник|среда|четверг|пятница|суббота|утром|вечером|завтра)",
            transcript, re.I
        )
        if time_match:
            time_pref = time_match.group(1).strip()

        # Проблема — берём из summary
        problem = summary if summary else "See transcript"

        text = (
            f"🔧 Новая заявка — Auto House UA\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 Имя: {name}\n"
            f"📱 Телефон: {caller}\n"
            f"🚗 Авто: {car}\n"
            f"📍 Локейшн: {location}\n"
            f"📅 Время: {time_pref}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💬 Проблема:\n{problem}\n"
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
