# EnSocial WhatsApp Sales Bot

Python starter for a real-estate sales chatbot that replies as Rahul from EnSocial, stores buyer chats, and extracts buyer personas.

## Files

- `engine.py` - chatbot reply generation, persona extraction, and CLI test mode.
- `server.py` - WhatsApp webhook server.
- `whatsapp.py` - WhatsApp Cloud API send-message helper.
- `storage.py` - JSON storage for chats, personas, and processed webhook message IDs.
- `prompts.py` - sales and persona extraction prompts.

## Setup

1. Create `.env` from the example:

```bash
cp .env.example .env
```

2. Fill these values in `.env`:

```bash
OPENAI_API_KEY=...
WHATSAPP_VERIFY_TOKEN=make_up_a_strong_verify_token
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_API_VERSION=v20.0
PORT=8000
```

3. Install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. Run the webhook server:

```bash
python server.py
```

5. Expose local server with ngrok:

```bash
ngrok http 8000
```

Use the HTTPS URL from ngrok as your webhook callback URL:

```text
https://your-ngrok-url.ngrok-free.app/webhook
```

## Meta WhatsApp Cloud API Setup

1. Open Meta Developers and create/select an app.
2. Add the WhatsApp product.
3. Copy the temporary or permanent access token into `WHATSAPP_ACCESS_TOKEN`.
4. Copy the test phone number ID into `WHATSAPP_PHONE_NUMBER_ID`.
5. In WhatsApp Webhooks, set:

```text
Callback URL: https://your-ngrok-url.ngrok-free.app/webhook
Verify token: same value as WHATSAPP_VERIFY_TOKEN
```

6. Subscribe to the `messages` webhook field.
7. Send a WhatsApp message to the Meta test number from an allowed recipient number.

## Local CLI Test

You can still test the bot without WhatsApp:

```bash
python engine.py
```

## Notes

- Meta may retry webhooks, so processed message IDs are stored in `data/processed_messages.json`.
- Replies split with `|||` are sent as separate WhatsApp messages.
- For production, use a real database, a permanent Meta token, logging, and a deployed HTTPS server instead of ngrok.
