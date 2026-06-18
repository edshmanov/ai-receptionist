from flask import Flask, request
import requests
import os
import json

app = Flask(__name__)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

BAD = ("", "none", "n/a", "null", "unknown", "не указано", "true", "false",
       "alex", "auto house ua", "autohouse ua")

def norm(k):
    return "".join(c for c in str(k).lower() if c.isalpha())

def walk(obj, flat):
    if isinstance(obj, dict):
        low = {k.lower(): k for k in obj if isinstance(k, str)}
        name_key = next((low[k] for k in ("name", "title", "key", "label") if k in low), None)
        val_key = next((low[k] for k in ("result", "value", "output") if k in low), None)
        if name_key and val_key and isinstance(obj.get(val_key), (str, int, float)):
            v = str(obj[val_key]).strip()
            if v.lower() not in BAD:
                flat[norm(obj[name_key])] = v
        for k, v in obj.items():
            if isinstance(v, (str, int, float)):
                s = str(v).strip()
                if norm(k) not in flat and s.lower() not in BAD:
                    flat[norm(k)] = s
            else:
                walk(v, flat)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, flat)

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

        flat = {}
        walk(data, flat)

        def pick(*cands):
            for c in cands:
                if c in flat and flat[c].lower() not in BAD:
                    return flat[c]
            return None

        name = pick("customername", "callername", "clientname", "fullname")
        car = pick("vehicle", "vehicletwo", "car", "carmodel", "vehicleinfo")
        location = pick("location", "shoplocation", "preferredlocation")
        time_pref = pick("appointmenttime", "preferredtime", "appointmentdatetime")
        problem = pick("problem", "issue", "concern", "servicereason")

        phone = caller if caller and caller != "Unknown" else (pick("phonenumber", "callbacknumber") or "Не указано")

        if not problem:
            transcript = msg.get("transcript", "")
            for line in transcript.split("\n"):
                line = line.strip()
                if line.lower().startswith("user:"):
                    t = line.split(":", 1)[1].strip()
                    if t:
                        problem = t[:120]
                        break

        def show(v):
            return v if v else "Не указано"

        text = (
            f"🔧 Новая заявка — Auto House UA\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 Имя: {show(name)}\n"
            f"📱 Телефон: {show(phone)}\n"
            f"🚗 Авто: {show(car)}\n"
            f"📍 Локейшн: {show(location)}\n"
            f"📅 Время: {show(time_pref)}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💬 Проблема: {show(problem)}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📲 CallMind AI"
        )

        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text[:4000]}
        )

        # Временный отладочный вывод — сработает только если поля пустые
        if not (name and car and location and time_pref):
            analysis = msg.get("analysis", {})
            dump = json.dumps(analysis, ensure_ascii=False)[:1500]
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": "🔍 DEBUG analysis:\n" + dump}
            )

    except Exception as e:
        print(f"Error: {e}")
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
