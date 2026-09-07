"""Offline lead + notify log demo without starting the HTTP server."""

from pathlib import Path

from config import DATABASE_PATH, NOTIFY_FALLBACK_PATH
from store import LeadStore


def main() -> None:
    for path in (DATABASE_PATH, NOTIFY_FALLBACK_PATH, Path("data/leads_export.csv")):
        if path.exists():
            path.unlink()

    store = LeadStore(DATABASE_PATH)
    samples = [
        {
            "visitor_name": "Jordan Lee",
            "email": "jordan@northwind.example",
            "channel": "whatsapp",
            "interest": "Website chat that also pings WhatsApp for sales",
            "budget": "$150-250",
        },
        {
            "visitor_name": "Sam Ortiz",
            "email": "sam@orbitshop.example",
            "channel": "slack",
            "interest": "Shopify store FAQ bot + Slack alerts",
            "budget": "$100",
        },
        {
            "visitor_name": "Casey Ng",
            "email": "casey@brightform.example",
            "channel": "messenger",
            "interest": "Facebook Messenger lead form without Zapier",
            "budget": "not sure",
        },
    ]

    print("Seeding sample leads...")
    for sample in samples:
        lead = store.add_lead(**sample)
        print(
            f"  #{lead.id} {lead.visitor_name} via {lead.channel} — {lead.interest}"
        )

    csv_path = Path("data/leads_export.csv")
    count = store.export_csv(csv_path)
    print(f"\nExported {count} leads -> {csv_path}")
    print("Open http://127.0.0.1:8790 after `uvicorn main:app --port 8790` for the widget demo.")
    store.close()


if __name__ == "__main__":
    main()
