import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from config import (
    NOTIFY_FALLBACK_PATH,
    SLACK_WEBHOOK_URL,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_TOKEN,
)
from store import LeadRecord


def _lead_text(lead: LeadRecord) -> str:
    return (
        f"New webchat lead #{lead.id}\n"
        f"Name: {lead.visitor_name}\n"
        f"Email: {lead.email}\n"
        f"Preferred channel: {lead.channel}\n"
        f"Interest: {lead.interest}\n"
        f"Budget: {lead.budget}"
    )


def _append_fallback(payload: dict) -> None:
    NOTIFY_FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with NOTIFY_FALLBACK_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


async def notify_slack(lead: LeadRecord) -> str:
    text = _lead_text(lead)
    if not SLACK_WEBHOOK_URL:
        _append_fallback(
            {
                "channel": "slack_fallback",
                "at": datetime.now(timezone.utc).isoformat(),
                "text": text,
            }
        )
        return "logged_locally"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(SLACK_WEBHOOK_URL, json={"text": text})
        if response.status_code >= 400:
            raise RuntimeError(
                f"Slack webhook failed: {response.status_code} {response.text[:200]}"
            )
    return "slack_ok"


async def notify_whatsapp_optional(lead: LeadRecord, to_phone_e164: str | None) -> str:
    """Optional Meta Cloud API ping to the business owner's phone, not the visitor."""
    if not to_phone_e164:
        return "skipped"
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        _append_fallback(
            {
                "channel": "whatsapp_fallback",
                "at": datetime.now(timezone.utc).isoformat(),
                "to": to_phone_e164,
                "text": _lead_text(lead),
            }
        )
        return "logged_locally"

    url = (
        f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    body = {
        "messaging_product": "whatsapp",
        "to": to_phone_e164.lstrip("+"),
        "type": "text",
        "text": {"body": _lead_text(lead)[:4000]},
    }
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(url, headers=headers, json=body)
        if response.status_code >= 400:
            raise RuntimeError(
                f"WhatsApp send failed: {response.status_code} {response.text[:300]}"
            )
    return "whatsapp_ok"
