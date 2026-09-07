import re

from faq import match_faq
from notify import notify_slack
from store import LeadStore

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CHANNELS = {"website", "whatsapp", "messenger", "slack", "email", "sms"}


def _welcome() -> str:
    return (
        "Hi — I can answer quick questions or take a project request.\n"
        "Type lead to start, or ask about pricing / WhatsApp / Slack / Zapier."
    )


async def handle_message(store: LeadStore, session_id: str, text: str) -> dict:
    cleaned = (text or "").strip()
    if not cleaned:
        return {"replies": ["Send a short message, or type lead."]}

    lowered = cleaned.lower()
    session = store.get_session(session_id)

    if lowered in {"help", "/help", "start", "/start", "hi", "hello"}:
        return {"replies": [_welcome()]}

    if lowered in {"cancel", "/cancel"}:
        store.clear_session(session_id)
        return {"replies": ["Cancelled. Type lead when you want to try again."]}

    if lowered in {"lead", "/lead"} and (session is None or session["step"] == "idle"):
        store.upsert_session(session_id, step="ask_name")
        return {"replies": ["Sure. What is your name?"]}

    if session and session["step"] != "idle":
        return await _continue_lead(store, session_id, session, cleaned)

    faq_reply = match_faq(cleaned)
    if faq_reply:
        return {"replies": [faq_reply]}

    return {
        "replies": [
            "I did not catch that. Ask about pricing, WhatsApp, Slack, Zapier — or type lead."
        ]
    }


async def _continue_lead(
    store: LeadStore, session_id: str, session: dict, cleaned: str
) -> dict:
    step = session["step"]

    if step == "ask_name":
        if len(cleaned) < 2:
            return {"replies": ["Name looks too short. Try again."]}
        store.upsert_session(session_id, step="ask_email", visitor_name=cleaned)
        return {"replies": ["Email address?"]}

    if step == "ask_email":
        if not EMAIL_RE.match(cleaned):
            return {"replies": ["That does not look like an email. Example: you@company.com"]}
        store.upsert_session(session_id, step="ask_channel", email=cleaned)
        return {
            "replies": [
                "Preferred follow-up channel? (website / whatsapp / messenger / slack / email / sms)"
            ]
        }

    if step == "ask_channel":
        channel = cleaned.lower().strip()
        if channel not in CHANNELS:
            return {
                "replies": [
                    "Pick one: website, whatsapp, messenger, slack, email, sms"
                ]
            }
        store.upsert_session(session_id, step="ask_interest", channel=channel)
        return {"replies": ["What do you need built? (one sentence)"]}

    if step == "ask_interest":
        if len(cleaned) < 8:
            return {"replies": ["A bit more detail, please."]}
        store.upsert_session(session_id, step="ask_budget", interest=cleaned)
        return {"replies": ["Budget range? (e.g. $100-200, or not sure)"]}

    if step == "ask_budget":
        if not cleaned:
            return {"replies": ["Budget cannot be empty. Type not sure if needed."]}
        latest = store.get_session(session_id) or session
        lead = store.add_lead(
            visitor_name=latest["visitor_name"],
            email=latest["email"],
            channel=latest["channel"],
            interest=latest["interest"],
            budget=cleaned,
        )
        store.clear_session(session_id)
        notify_status = await notify_slack(lead)
        return {
            "replies": [
                f"Thanks {lead.visitor_name}. Lead #{lead.id} saved.",
                f"Notify: {notify_status}. We will follow up on {lead.channel}.",
            ],
            "lead_id": lead.id,
        }

    store.clear_session(session_id)
    return {"replies": ["Session reset. Type lead to start again."]}
