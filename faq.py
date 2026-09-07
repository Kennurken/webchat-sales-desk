from dataclasses import dataclass


@dataclass(frozen=True)
class FaqHit:
    keywords: tuple[str, ...]
    reply: str


FAQ = (
    FaqHit(
        ("price", "pricing", "cost", "how much"),
        "Starter website chat + lead capture is usually in the Basic range. "
        "WhatsApp/Messenger Business setup is Standard/Premium because of Meta review.",
    ),
    FaqHit(
        ("whatsapp", "messenger", "instagram"),
        "Yes — same lead flow can fan out to WhatsApp Cloud API, Messenger, or Slack. "
        "This demo widget is the website channel; WhatsApp needs a Meta Business app token.",
    ),
    FaqHit(
        ("slack", "email", "notify"),
        "When a lead is complete, the server posts to a Slack webhook (or writes a local "
        "notify log if no webhook is set). Email can be added the same way.",
    ),
    FaqHit(
        ("zapier", "make", "n8n"),
        "No Zapier required. The widget talks to your own API. You can still forward "
        "events to Make/n8n later if you want.",
    ),
    FaqHit(
        ("dialogflow", "rasa", "nlp", "ai"),
        "This sample is rule-based (FAQ keywords + guided lead form). Dialogflow/Rasa "
        "can replace the FAQ matcher without changing the widget.",
    ),
)


def match_faq(text: str) -> str | None:
    lowered = text.lower()
    for hit in FAQ:
        if any(word in lowered for word in hit.keywords):
            return hit.reply
    return None
