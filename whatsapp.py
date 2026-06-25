import mimetypes
import os

import requests
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_API_VERSION = os.environ.get("WHATSAPP_API_VERSION", "v20.0")
WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")


def _require_credentials():
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        raise RuntimeError("Missing WhatsApp API credentials in environment")


def _messages_url():
    return (
        f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )


def _auth_headers():
    return {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}


def send_whatsapp_text(to_phone, text):
    _require_credentials()

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text},
    }
    headers = {
        **_auth_headers(),
        "Content-Type": "application/json",
    }

    response = requests.post(_messages_url(), json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def send_whatsapp_attachment(to_phone, attachment):
    _require_credentials()

    media_type = attachment.get("type", "document")
    media_id = upload_whatsapp_media(attachment["path"])

    media_payload = {"id": media_id}
    caption = attachment.get("caption")
    if caption and media_type in {"document", "image", "video"}:
        media_payload["caption"] = caption

    if media_type == "document":
        media_payload["filename"] = attachment.get("file") or os.path.basename(attachment["path"])

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": media_type,
        media_type: media_payload,
    }
    headers = {
        **_auth_headers(),
        "Content-Type": "application/json",
    }

    response = requests.post(_messages_url(), json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def upload_whatsapp_media(file_path):
    _require_credentials()

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Attachment file not found: {file_path}")

    url = (
        f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/media"
    )
    mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    data = {
        "messaging_product": "whatsapp",
        "type": mime_type,
    }

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, mime_type)}
        response = requests.post(
            url,
            data=data,
            files=files,
            headers=_auth_headers(),
            timeout=30,
        )

    response.raise_for_status()
    return response.json()["id"]
