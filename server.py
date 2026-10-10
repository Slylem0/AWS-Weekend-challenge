"""FastAPI server for Dr. Cloud. Works on AWS App Runner (plain HTTP, no WebSockets)."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from agent import create_agent, friendly_error

app = FastAPI(title="Dr. Cloud")

# One agent instance reused across requests.
_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


class Question(BaseModel):
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(q: Question):
    text = (q.message or "").strip()
    if not text:
        return JSONResponse({"reply": "Cuéntame qué error de AWS te trae por aquí 🩺"})
    try:
        reply = str(get_agent()(text))
    except Exception as exc:  # noqa: BLE001 - turn into Dr. Cloud's bedside manner
        reply = friendly_error(exc)
    return JSONResponse({"reply": reply})


@app.get("/", response_class=HTMLResponse)
def index():
    return (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
