from flask import Flask, request
import requests
import os

app = Flask(__name__)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

BAD = ("", "none", "n/a", "null", "unknown", "не указано", "true", "false")

def norm(k):
    return "".join(c for c in str(k).lower() if c.isalpha() or c == "_").replace("_", "")

def collect(obj, flat):
    """Рекурсивно собираем все пары имя→значение, включая формат name/result."""
    if isinstance(obj, dict):
        low = {k.lower(): k for k in obj if isinstance(k, str)}
        nk = next((low[k] for k in ("name", "title", "key", "label") if k in low), None)
        vk = next((low[k] for k in ("result", "value", "output") if k in low), None)
        if nk and vk and isinstance(obj.get(vk), (str, int, float)):
            v = str(obj[vk]).strip()
            if v.lower() not in BAD:
                flat[norm(obj[nk])] = v
        for k, v in obj.items():
            if isinstance(v, (str, int, float)):
                s = str(v).strip()
                if norm(k) not in flat and s.lower() not in BAD:
                    flat[norm(k)] = s
            else:
                collect(v, flat)
    elif isinstance(obj, list):
        for v in obj:
            collect(v, flat)

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
        collect(data, flat)

        def pick(*cands):
            for c in cands:
                key = norm(c)
                if key in flat and flat[key].lower() not in BAD:
                    return flat[key]
            return None

        name = pick("customer_name", "customername")
        car = pick("vehicle_text", "vehicletext")
        location = pick("location")
        time_pref = pick("appointment_time", "appointmenttime")
        problem = pick("problem")

        phone = caller if caller and caller != "Unknown" else "Не указано"

        # подстраховка для проблемы из транскрипта
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
    except Exception as e:
        print(f"Error: {e}")
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
