from flask import Flask, request
import requests
import os
import re

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def parse(transcript):
    name, address, service, time = "Not provided", "Not provided", "Not provided", "Not provided"
    lines = transcript.split("\n")
    for line in lines:
        low = line.lower()
        if "ai:" not in low:
            continue
        if "name" in low and "elder" in low.replace("ai:",""):
            m = re.search(r'name[,\s]+(\w[\w\s]+)', line, re.I)
            if m: name = m.group(1).strip()
        if any(x in low for x in ["address is", "that's", "zip code"]):
            m = re.search(r'(?:address is|that\'s|so that\'s)\s+(.+?)(?:\.|,|zip)', line, re.I)
            if m: address = m.group(1).strip()
        if any(x in low for x in ["tomorrow", "monday","tuesday","wednesday","thursday","friday","at 10","at 9","am","pm"]):
            m = re.search(r'(tomorrow[^.]+|(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)[^.]+)', line, re.I)
            if m: time = m.group(1).strip()

    # Find summary block - AI usually summarizes at the end
    full = transcript
    summary_match = re.search(r'name[,\s:]+([A-Z][a-z]+ [A-Z][a-z]+)', full)
    if summary_match: name = summary_match.group(1)

    address_match = re.search(r'(\d+\s+\w[\w\s]+(?:street|st|ave|avenue|rd|road|blvd|north|south|east|west|way|drive|dr|ln|lane)[^,.\n]*)', full, re.I)
    if address_match: address = address_match.group(1).strip()

    zip_match = re.search(r'zip\s*(?:code)?\s*(?:is\s+)?(\d{5})', full, re.I)
    if zip_match and address != "Not provided":
        address += f", ZIP {zip_match.group(1)}"

    time_match = re.search(r'(tomorrow[^.\n]+|(?:monday|tuesday|wednesday|thursday|friday)[^.\n]+)', full, re.I)
    if time_match: time = time_match.group(1).strip()

    service_match = re.search(r'(plumbing|pipe|leak|roof|electric|handyman|repair|install|fix)[^.\n]{0,60}', full, re.I)
    if service_match: service = service_match.group(0).strip()

    return name, address, service, time


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
    name, address, service, time = parse(transcript)
    text = (
        f"📞 New Lead!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 Name: {name}\n"
        f"📱 Phone: {caller}\n"
        f"📍
