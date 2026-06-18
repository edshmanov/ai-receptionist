from flask import Flask, request
import requests
import os
import re

app = Flask(__name__)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

BAD = ("", "none", "n/a", "null", "unknown", "не указано", "alex", "auto house ua", "autohouse ua")

def norm(k):
    return re.sub(r"[^a-z]", "", str(k).lower())

def deep_find(obj, keys):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if norm(k) in keys and isinstance(v, (str, int, float)):
                s = str(v).strip()
                if s.lower() not in BAD:
                    return s
        for v in obj.values():
            r = deep_find(v, keys)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = deep_find(v, keys)
            if r:
                return r
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

        name = deep_find(data, {"customername", "callername", "clientname", "fullname"}) or "Не указано"
        car = deep_find(data, {"vehicle", "car", "vehicleinfo", "carmodel"}) or "Не указано"
        location = deep_find(data, {"location", "shoplocation", "preferredlocation"}) or "Не указано"
        time_pref = deep_find(data, {"appointmenttime", "preferredtime", "appointmentdatetime"}) or "Не указано"
        problem = deep_find(data, {"problem", "issue", "concern", "servicereason"}) or "Не указано"

        phone = deep_find(data, {"phonenumber", "callbacknumber", "customerphone"})
        if caller and caller != "Unknown":
            phone = caller
        if not phone:
            phone = "Не указано"

        # Подстраховка для проблемы — первая фраза клиента
        if problem == "Не указано":
            transcript = msg.get("transcript", "")
            for line in transcript.split("\n"):
                line = line.strip()
                if line.lower().startswith("user:"):
                    t = line.split(":", 1)[1].strip()
                    if t:
                        problem = t[:120]
                        break

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
