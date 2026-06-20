from flask import Flask, request
import requests
import os
import re

app = Flask(__name__)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

BRANDS = "BMW|Porsche|Mercedes|Toyota|Audi|Honda|Ford|Chevrolet|Chevy|Lexus|Nissan|Hyundai|Kia|Volkswagen|VW|Subaru|Mazda|Dodge|Ram|Jeep|GMC|Cadillac|Infiniti|Acura|Volvo|Tesla|Land Rover|Range Rover"
WORDNUM = {"one":"1","two":"2","three":"3","four":"4","five":"5","six":"6","seven":"7","eight":"8","nine":"9","ten":"10","eleven":"11","twelve":"12"}

def parse_lines(transcript):
    lines = []
    for raw in transcript.split("\n"):
        raw = raw.strip()
        if not raw or ":" not in raw:
            continue
        role, text = raw.split(":", 1)
        lines.append((role.strip().lower(), text.strip()))
    return lines

def next_user_reply(lines, idx):
    for j in range(idx + 1, len(lines)):
        role, text = lines[j]
        if role == "user" and text:
            return text
    return None

def find_answer(lines, ai_keywords):
    for i, (role, text) in enumerate(lines):
        if role in ("ai", "assistant", "bot") and any(k in text.lower() for k in ai_keywords):
            reply = next_user_reply(lines, i)
            if reply:
                return reply
    return None

def first_user_reply(lines):
    for role, text in lines:
        if role == "user" and text:
            return text
    return None

def clean_name(text):
    if not text:
        return None
    m = re.search(r"(?:my name is|this is|it's|i am|i'm|меня зовут)\s+([A-Za-zА-Яа-я]+(?:\s+[A-Za-zА-Яа-я]+)?)", text, re.I)
    if m:
        return m.group(1).strip().title()
    m = re.search(r"^([A-Za-zА-Яа-я]+(?:\s+[A-Za-zА-Яа-я]+)?)", text.strip())
    if m:
        return m.group(1).strip().title()
    return None

def clean_car(text):
    if not text:
        return None
    m = re.search(r"(\d{4})\s*(" + BRANDS + r")([A-Za-z0-9\- ]{0,18})", text, re.I)
    if m:
        return (m.group(1) + " " + m.group(2) + m.group(3)).strip()
    m = re.search(r"(" + BRANDS + r")([A-Za-z0-9\- ]{0,18})", text, re.I)
    if m:
        return (m.group(1) + m.group(2)).strip()
    return text[:60].strip()

def clean_location(text, full):
    src = (text or "") + " " + full
    if "arlington" in src.lower():
        return "Arlington Heights"
    if "schaumburg" in src.lower():
        return "Schaumburg"
    return None

def clean_time(text):
    if not text:
        return None
    t = text
    for w, d in WORDNUM.items():
        t = re.sub(rf"\b{w}\b", d, t, flags=re.I)
    m = re.search(r"((?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow)[\sA-Za-z0-9,:']{0,30}(?:am|pm))", t, re.I)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    m = re.search(r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow)", t, re.I)
    if m:
        return m.group(1).strip().capitalize()
    return t[:40].strip()

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
        full = transcript.replace("\n", " ")
        lines = parse_lines(transcript)

        name_raw = find_answer(lines, ["name"])
        car_raw = find_answer(lines, ["year", "make", "model"])
        location_raw = find_answer(lines, ["schaumburg", "arlington", "location", "convenient"])
        time_raw = find_answer(lines, ["day", "time works", "time"])
        problem_raw = first_user_reply(lines)

        name = clean_name(name_raw) or "Не указано"
        car = clean_car(car_raw) or "Не указано"
        location = clean_location(location_raw, full) or "Не указано"
        time_pref = clean_time(time_raw) or "Не указано"
        problem = (problem_raw[:150].strip() if problem_raw else None) or "Не указано"

        phone = caller if caller and caller != "Unknown" else "Не указано"

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
