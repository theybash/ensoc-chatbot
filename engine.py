import json
import os
import sys
import time
import random

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from prompts import SYSTEM_PROMPT, PERSONA_EXTRACTION_PROMPT
from storage import load_chat, save_chat, append_message, load_persona, save_persona

MODEL = "gpt-5.1-mini"

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def generate_reply(chat_history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in chat_history:
        messages.append({
            "role": "user" if m["role"] == "user" else "assistant",
            "content": m["content"]
        })

    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.9,
        max_tokens=300,
    )
    return resp.choices[0].message.content


def extract_persona(chat_history, phone):
    convo = "\n".join(
        f"{'Buyer' if m['role'] == 'user' else 'Rahul'}: {m['content']}"
        for m in chat_history
    )

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PERSONA_EXTRACTION_PROMPT},
            {"role": "user", "content": f"Phone: {phone}\n\nConversation:\n{convo}"},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    try:
        return json.loads(resp.choices[0].message.content)
    except json.JSONDecodeError:
        return None


def print_typing(text):
    """Simulate typing for multi-message replies split by |||"""
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    for i, part in enumerate(parts):
        if i > 0:
            time.sleep(random.uniform(0.5, 1.5))
        print(f"\033[92mRahul:\033[0m {part}")


def print_persona(persona):
    if not persona:
        print("\033[93m[No persona data yet]\033[0m")
        return

    print("\n\033[96m{'='*50}")
    print("  BUYER PERSONA")
    print(f"{'='*50}\033[0m")
    print(f"  Name:     {persona.get('name') or '???'}")
    print(f"  Number:   {persona.get('number') or '???'}")

    intent = persona.get("intent", {})
    print(f"  Intent:   {intent.get('score', '?')}% (confidence: {intent.get('confidence', '?')}%)")
    print(f"            {intent.get('reasoning', '')}")

    fam = persona.get("family_size", {})
    print(f"  Family:   ~{fam.get('estimate', '?')} people (confidence: {fam.get('confidence', '?')}%)")
    print(f"            {fam.get('reasoning', '')}")

    config = persona.get("configuration", {})
    print(f"  Config:   {config.get('bhk') or '???'} (confidence: {config.get('confidence', '?')}%)")
    print(f"            {config.get('reasoning', '')}")

    loc = persona.get("preferred_location", {})
    areas = ", ".join(loc.get("areas", [])) or "???"
    print(f"  Location: {areas} (confidence: {loc.get('confidence', '?')}%)")
    print(f"            {loc.get('reasoning', '')}")

    budget = persona.get("budget", {})
    print(f"  Budget:   {budget.get('range') or '???'} (confidence: {budget.get('confidence', '?')}%)")
    print(f"            {budget.get('reasoning', '')}")

    timeline = persona.get("timeline", {})
    print(f"  Timeline: {timeline.get('estimate') or '???'} (confidence: {timeline.get('confidence', '?')}%)")
    print(f"            {timeline.get('reasoning', '')}")

    notes = persona.get("notes")
    if notes:
        print(f"  Notes:    {notes}")

    print(f"\033[96m{'='*50}\033[0m\n")


def main():
    phone = input("Enter buyer phone number (for tracking): ").strip()
    if not phone:
        phone = "unknown"

    print(f"\n\033[93mChat session for {phone}")
    print("Commands: /persona = show persona, /clear = reset chat, /quit = exit\033[0m")
    print("-" * 40)

    history = load_chat(phone)
    if history:
        print(f"\033[93m[Loaded {len(history)} previous messages]\033[0m")
        for m in history[-10:]:
            if m["role"] == "user":
                print(f"\033[94mBuyer:\033[0m {m['content']}")
            else:
                print(f"\033[92mRahul:\033[0m {m['content']}")
        print("-" * 40)

    if not history:
        reply = generate_reply([])
        history = append_message(phone, "assistant", reply)
        print_typing(reply)

    while True:
        try:
            user_input = input(f"\033[94mBuyer:\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input == "/persona":
            persona = load_persona(phone)
            if not persona and len(history) >= 2:
                print("\033[93m[Extracting persona...]\033[0m")
                persona = extract_persona(history, phone)
                if persona:
                    persona["number"] = phone
                    save_persona(phone, persona)
            print_persona(persona)
            continue

        if user_input == "/clear":
            save_chat(phone, [])
            save_persona(phone, {})
            history = []
            print("\033[93m[Chat and persona cleared]\033[0m")
            reply = generate_reply([])
            history = append_message(phone, "assistant", reply)
            print_typing(reply)
            continue

        if user_input == "/quit":
            break

        history = append_message(phone, "user", user_input)

        reply = generate_reply(history)
        history = append_message(phone, "assistant", reply)
        print_typing(reply)

        if len(history) % 6 == 0:
            persona = extract_persona(history, phone)
            if persona:
                persona["number"] = phone
                save_persona(phone, persona)
                print("\033[93m[Persona updated silently]\033[0m")

    print("\n\033[93m[Final persona extraction...]\033[0m")
    persona = extract_persona(history, phone)
    if persona:
        persona["number"] = phone
        save_persona(phone, persona)
        print_persona(persona)

    print(f"\033[93mChat saved to data/chats/{phone}.json\033[0m")
    print(f"\033[93mPersona saved to data/personas/{phone}.json\033[0m")


if __name__ == "__main__":
    main()
