import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CHATS_DIR = os.path.join(DATA_DIR, "chats")
PERSONAS_DIR = os.path.join(DATA_DIR, "personas")
PROCESSED_MESSAGES_PATH = os.path.join(DATA_DIR, "processed_messages.json")

os.makedirs(CHATS_DIR, exist_ok=True)
os.makedirs(PERSONAS_DIR, exist_ok=True)


def _sanitize(phone):
    sanitized = "".join(c for c in phone if c.isdigit())
    return sanitized or "unknown"


def _chat_path(phone):
    return os.path.join(CHATS_DIR, f"{_sanitize(phone)}.json")


def _persona_path(phone):
    return os.path.join(PERSONAS_DIR, f"{_sanitize(phone)}.json")


def load_chat(phone):
    path = _chat_path(phone)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def save_chat(phone, messages):
    with open(_chat_path(phone), "w") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)


def append_message(phone, role, content):
    messages = load_chat(phone)
    messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    save_chat(phone, messages)
    return messages


def load_persona(phone):
    path = _persona_path(phone)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def save_persona(phone, persona):
    with open(_persona_path(phone), "w") as f:
        json.dump(persona, f, indent=2, ensure_ascii=False)


def has_processed_message(message_id):
    if not message_id or not os.path.exists(PROCESSED_MESSAGES_PATH):
        return False

    with open(PROCESSED_MESSAGES_PATH) as f:
        processed = json.load(f)
    return message_id in processed


def mark_message_processed(message_id):
    if not message_id:
        return

    processed = []
    if os.path.exists(PROCESSED_MESSAGES_PATH):
        with open(PROCESSED_MESSAGES_PATH) as f:
            processed = json.load(f)

    if message_id not in processed:
        processed.append(message_id)

    with open(PROCESSED_MESSAGES_PATH, "w") as f:
        json.dump(processed[-1000:], f, indent=2)
