import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from engine import handle_user_message
from storage import has_processed_message, mark_message_processed
from whatsapp import send_whatsapp_text

load_dotenv()

app = Flask(__name__)

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
            replies = handle_user_message(phone, text)
            for reply in replies:
                send_whatsapp_text(phone, reply)
        except Exception:
            app.logger.exception("Failed to process WhatsApp message %s", message_id)
            send_whatsapp_text(phone, FALLBACK_REPLY)

        mark_message_processed(message_id)

    return jsonify({"ok": True})


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
