# Webchat sales desk

Website chat widget for small shops / freelancers:

- floating widget on a demo storefront
- keyword FAQ (pricing, WhatsApp, Slack, Zapier, Dialogflow)
- guided `lead` intake → SQLite
- Slack webhook notify (or local `data/notify_log.jsonl` if unset)
- optional WhatsApp Cloud API hook for owner alerts
- `/api/leads` + CSV export

Built for US-facing Fiverr demos (website / WhatsApp / Messenger / Slack), not Telegram-first.

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

uvicorn main:app --host 127.0.0.1 --port 8790
```

Open http://127.0.0.1:8790 — click **Chat with sales**.

## Offline sample data

```bash
python demo_sim.py
```

## Example chat

```
user: lead
bot: What is your name?
user: Jordan Lee
bot: Email address?
...
bot: Thanks Jordan Lee. Lead #1 saved.
bot: Notify: logged_locally. We will follow up on whatsapp.
```

## Slack / WhatsApp

Set in `.env`:

- `SLACK_WEBHOOK_URL` — incoming webhook
- `WHATSAPP_TOKEN` + `WHATSAPP_PHONE_NUMBER_ID` — Meta Cloud API (optional)

Without them, notifications append to `data/notify_log.jsonl` so demos still work.

## Known limitations

- FAQ is keyword matching; swap in Dialogflow/Rasa for NLU.
- WhatsApp visitor chat needs Meta Business + webhook verify — this repo notifies the owner, it is not a full inbox.
- Messenger/Instagram are the same pattern as WhatsApp (Graph API), not fully wired here.

## Screenshots

See `screenshots/` in this repo (also copied to `../screenshots/webchat-sales-desk/` for Fiverr Gallery):

- storefront
- chat widget lead flow
- leads table / CSV
- Slack-style notify card
