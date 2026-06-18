from flask import Flask, request
import requests
import os
import re

app = Flask(__name__)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def user_text(transcript):
    lines = []
    for line in transcript.split("\n"):
        line = line.strip()
        if line.lower().startswith("user:"):
            t = line.split(":", 1)[1].strip()
            if t:
                lines.append(t)
    return " ".join(lines)

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
        u = user_text(transcript)

        # Имя: ищем разные формы
        name = "Не указано"
        m = re.search(r"(?:my name is|i am|i'm|this is|name is|it's|меня зовут)\s+([A-Za-zА-Яа-я]+(?:\s+[A-Za-zА-Яа-я]+)?)", u, re.I)
        if not m:
            # имя как ответ из 1-2 слов с заглавных, без цифр и служебных слов
            m = re.search(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", u)
            if m and m.group(1).lower() in ("arlington","schaumburg","friday","monday","tuesday","wednesday","thursday","saturday","porsche","bmw","mercedes","toyota","audi","honda"):
                m = None
        if m:
            name = m.group(1).strip().title()

        # Машина: год+марка ИЛИ просто марка
        car = "Не указано"
        brands = "BMW|Porsche|Mercedes|Toyota|Audi|Honda|Ford|Chevrolet|Lexus|Nissan|Hyundai|Kia|Volkswagen|VW|Subaru|Mazda|Dodge|Ram|Jeep|GMC|Cadillac|Infiniti|Acura|Volvo|Tesla|Land Rover|Range Rover"
        m = re.search(r"(\d{4})\s+(" + brands + r")([A-Za-z0-9 ]{0,15})", u, re.I)
        if m:
            car = (m.group(1) + " " + m.group(2) + m.group(3)).strip()
        else:
            m = re.search(r"(" + brands + r")([A-Za-z0-9 ]{0,15})", u, re.I)
            if m:
                car = (m.group(1) + m.group(2)).strip()

        phone = caller if caller and caller != "Unknown" else "Не указано"

        location = "Не указано"
        if "arlington" in u.lower():
            location = "Arlington Heights"
        elif "schaumburg" in u.lower():
            location = "Schaumburg"

        time_pref = "Не указано"
        m = re.search(r"((?:monday|tuesday|wednesday|thursday|friday|saturday|tomorrow)[A-Za-z0-9 :]{0,20}(?:am|pm)?)", u, re.I)
        if m:
            time_pref = m.group(1).strip()

        problem = "Не указано"
        pm = re.search(r"(brake[s]?|engine|transmission|oil|noise|check engine|battery|tire[s]?|suspension|coolant|leak|ac|air condition|diagnos[a-z]*|tuning|light[s]?)[A-Za-z ,]{0,40}", u, re.I)
        if pm:
            problem = pm.group(0).strip()
        elif u:
            problem = u[:120]

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
