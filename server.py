import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

from engine import handle_user_message, update_persona_if_ready
from storage import (
    CHATS_DIR,
    PERSONAS_DIR,
    has_processed_message,
    load_chat,
    load_persona,
    mark_message_processed,
    save_chat,
    save_persona,
)
from whatsapp import send_whatsapp_text

load_dotenv()

app = Flask(__name__)

DASHBOARD_DIR = os.path.join(os.path.dirname(__file__), "dashboard")


@app.after_request
def add_cors_headers(response):
    if request.path.startswith("/api/"):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, ngrok-skip-browser-warning"
    return response

VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN")
FALLBACK_REPLY = os.environ.get(
    "FALLBACK_REPLY",
    "Thanks for your message. Rahul from EnSocial here, I will check and get back to you shortly.",
)


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge or "", 200

    return "Forbidden", 403


@app.post("/webhook")
def receive_webhook():
    payload = request.get_json(silent=True) or {}

    for message in _extract_text_messages(payload):
        message_id = message["id"]
        if has_processed_message(message_id):
            continue

        phone = message["from"]
        text = message["text"]

        try:
            replies = handle_whatsapp_text(phone, text)
            for reply in replies:
                send_whatsapp_text(phone, reply)
        except Exception:
            app.logger.exception("Failed to process WhatsApp message %s", message_id)
            send_whatsapp_text(phone, FALLBACK_REPLY)

        mark_message_processed(message_id)

    return jsonify({"ok": True})


def handle_whatsapp_text(phone, text):
    command = text.strip().lower()

    if command == "/persona":
        return [get_persona_reply(phone)]

    if command == "/clear":
        save_chat(phone, [])
        save_persona(phone, {})
        return ["Chat cleared. I have reset this number's chat history and buyer persona."]

    return handle_user_message(phone, text)


def get_persona_reply(phone):
    persona = load_persona(phone)
    history = load_chat(phone)

    if not persona and len(history) >= 2:
        persona = update_persona_if_ready(phone, history, force=True)

    if not persona:
        return (
            "No buyer persona yet for this number. "
            "Once we have a bit more conversation, send /persona again."
        )

    return format_persona_for_whatsapp(persona)


def format_persona_for_whatsapp(persona):
    intent = persona.get("intent", {})
    family = persona.get("family_size", {})
    configuration = persona.get("configuration", {})
    location = persona.get("preferred_location", {})
    budget = persona.get("budget", {})
    timeline = persona.get("timeline", {})

    location_areas = location.get("areas", [])
    if isinstance(location_areas, list):
        location_text = ", ".join(location_areas) or "Unknown"
    else:
        location_text = location_areas or "Unknown"

    lines = [
        "Buyer persona",
        f"Name: {persona.get('name') or 'Unknown'}",
        f"Number: {persona.get('number') or 'Unknown'}",
        f"Intent: {_format_scored_value(intent)}",
        f"Family: {_format_scored_value(family, 'estimate')}",
        f"Config: {_format_scored_value(configuration, 'bhk')}",
        f"Location: {location_text} ({location.get('confidence', '?')}% confidence)",
        f"Budget: {_format_scored_value(budget, 'range')}",
        f"Timeline: {_format_scored_value(timeline, 'estimate')}",
    ]

    notes = persona.get("notes")
    if notes:
        lines.append(f"Notes: {notes}")

    return "\n".join(lines)


def _format_scored_value(section, value_key="score"):
    value = section.get(value_key)
    confidence = section.get("confidence", "?")

    if value is None or value == "":
        value = "Unknown"

    if value_key == "score" and value != "Unknown":
        value = f"{value}%"

    return f"{value} ({confidence}% confidence)"


@app.get("/")
@app.get("/dashboard")
def dashboard():
    return send_from_directory(DASHBOARD_DIR, "index.html")


@app.get("/api/personas")
def list_personas():
    return jsonify({"leads": [_lead_summary(phone) for phone in _all_phones()]})


@app.get("/api/personas/<phone>")
def persona_detail(phone):
    sanitized = "".join(c for c in phone if c.isdigit()) or "unknown"
    if sanitized not in _all_phones():
        return jsonify({"error": "not found"}), 404

    return jsonify({
        "summary": _lead_summary(sanitized),
        "persona": load_persona(sanitized),
        "chat": load_chat(sanitized),
    })


def _all_phones():
    phones = set()
    for directory in (PERSONAS_DIR, CHATS_DIR):
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                phones.add(filename[:-5])
    return sorted(phones)


def _lead_summary(phone):
    persona = load_persona(phone) or {}
    chat = load_chat(phone)

    intent = persona.get("intent") or {}
    budget = persona.get("budget") or {}
    configuration = persona.get("configuration") or {}
    location = persona.get("preferred_location") or {}
    timeline = persona.get("timeline") or {}
    family = persona.get("family_size") or {}

    areas = location.get("areas") or []
    if not isinstance(areas, list):
        areas = [areas]

    return {
        "phone": phone,
        "name": persona.get("name"),
        "intent_score": intent.get("score"),
        "intent_confidence": intent.get("confidence"),
        "budget": budget.get("range"),
        "configuration": configuration.get("bhk"),
        "locations": areas,
        "timeline": timeline.get("estimate"),
        "family_size": family.get("estimate"),
        "notes": persona.get("notes"),
        "has_persona": bool(persona),
        "message_count": len(chat),
        "last_message_at": chat[-1].get("timestamp") if chat else None,
        "last_message_role": chat[-1].get("role") if chat else None,
    }


def _extract_text_messages(payload):
    messages = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                text = message.get("text", {}).get("body")
                message_id = message.get("id")
                from_phone = message.get("from")
                if message.get("type") != "text" or not text or not message_id or not from_phone:
                    continue

                messages.append({
                    "id": message_id,
                    "from": from_phone,
                    "text": text,
                })
    return messages


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
