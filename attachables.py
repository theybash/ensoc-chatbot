import os
import re


BASE_DIR = os.path.dirname(__file__)
ATTACHABLES_DIR = os.path.join(BASE_DIR, "attachables")
ATTACHABLES_MD = os.path.join(ATTACHABLES_DIR, "attachables.md")


def load_attachables():
    if not os.path.exists(ATTACHABLES_MD):
        return []

    with open(ATTACHABLES_MD) as f:
        content = f.read()

    attachables = []
    current = None

    for line in content.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            if current:
                attachables.append(_normalize_attachable(current))
            current = {"id": _slugify(heading.group(1)), "title": heading.group(1).strip()}
            continue

        if not current or ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key in {"id", "file", "type", "title", "description", "caption", "keywords"}:
            current[key] = value

    if current:
        attachables.append(_normalize_attachable(current))

    return [
        a
        for a in attachables
        if a.get("id") and a.get("file") and os.path.exists(a.get("path", ""))
    ]


def get_attachable(attachment_id):
    for attachable in load_attachables():
        if attachable["id"] == attachment_id:
            return attachable
    return None


def attachables_tool_spec():
    attachables = load_attachables()
    if not attachables:
        return None

    return {
        "type": "function",
        "function": {
            "name": "send_attachment",
            "description": (
                "Send one relevant local sales attachment to the buyer on WhatsApp. "
                "Use this only when the buyer asks for a brochure, floor plan, price sheet, "
                "map, payment plan, layout, or another available file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "attachment_id": {
                        "type": "string",
                        "enum": [a["id"] for a in attachables],
                        "description": "The id of the attachment to send.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Short reason why this attachment is relevant.",
                    },
                },
                "required": ["attachment_id"],
                "additionalProperties": False,
            },
        },
    }


def attachables_prompt_context():
    attachables = load_attachables()
    if not attachables:
        return ""

    lines = [
        "",
        "AVAILABLE FILE ATTACHMENTS:",
        "When the buyer asks for a relevant file, call the send_attachment tool.",
        "Do not claim a file is attached unless you call the tool.",
    ]

    for attachable in attachables:
        keywords = ", ".join(attachable.get("keywords", [])) or "none"
        lines.append(
            f"- {attachable['id']}: {attachable['title']} "
            f"({attachable['type']}) — {attachable.get('description') or 'No description'} "
            f"Keywords: {keywords}"
        )

    return "\n".join(lines)


def _normalize_attachable(attachable):
    normalized = dict(attachable)
    normalized["id"] = _slugify(normalized.get("id") or normalized.get("title") or "")
    normalized["title"] = normalized.get("title") or normalized["id"]
    normalized["type"] = (normalized.get("type") or "document").lower()
    normalized["file"] = normalized.get("file", "").strip()
    normalized["path"] = os.path.join(ATTACHABLES_DIR, normalized["file"])
    normalized["keywords"] = [
        keyword.strip().lower()
        for keyword in normalized.get("keywords", "").split(",")
        if keyword.strip()
    ]
    return normalized


def _slugify(value):
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")
