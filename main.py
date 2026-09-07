from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from chat_flow import handle_message
from config import DATABASE_PATH, HOST, PORT
from store import LeadStore

ROOT = Path(__file__).resolve().parent
store = LeadStore(DATABASE_PATH)
app = FastAPI(title="Webchat sales desk")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=4, max_length=80)
    message: str = Field(min_length=1, max_length=2000)


@app.get("/")
def demo_page():
    return FileResponse(ROOT / "static" / "demo.html")


@app.get("/leads-ui")
def leads_ui():
    return FileResponse(ROOT / "static" / "leads.html")


@app.get("/slack-mock")
def slack_mock():
    return FileResponse(ROOT / "static" / "slack-mock.html")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/chat")
async def api_chat(body: ChatRequest):
    result = await handle_message(store, body.session_id, body.message)
    return result


@app.get("/api/leads")
def api_leads():
    leads = store.list_recent(30)
    return [
        {
            "id": lead.id,
            "created_at": lead.created_at,
            "visitor_name": lead.visitor_name,
            "email": lead.email,
            "channel": lead.channel,
            "interest": lead.interest,
            "budget": lead.budget,
            "status": lead.status,
        }
        for lead in leads
    ]


@app.post("/api/export")
def api_export():
    csv_path = ROOT / "data" / "leads_export.csv"
    count = store.export_csv(csv_path)
    if count == 0:
        raise HTTPException(status_code=404, detail="No leads to export")
    return FileResponse(
        csv_path,
        media_type="text/csv",
        filename="leads_export.csv",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
