import hmac
import hashlib
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import Base, engine, SessionLocal
from schemas import WebhookMessage
from service import upsert_message, seed_demo_data
from models import Conversation

load_dotenv()
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "troque_essa_chave")

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    yield

app = FastAPI(title="Kommo Conversas API", lifespan=lifespan)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_signature(body: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    digest = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha1).hexdigest()
    return hmac.compare_digest(digest, signature)


@app.get("/")
def root(db: Session = Depends(get_db)):
    return {
        "status": "ok",
        "conversations": db.query(Conversation).count(),
        "message": "API pronta para receber webhooks do Kommo"
    }


@app.post("/webhook/kommo")
async def receive_kommo_webhook(
    request: Request,
    x_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    raw_body = await request.body()

    # Para testar localmente sem assinatura real, comente a validação abaixo.
    if WEBHOOK_SECRET != "desabilitar" and not validate_signature(raw_body, x_signature):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = WebhookMessage.model_validate_json(raw_body)
    conversation = upsert_message(db, payload)
    return {
        "ok": True,
        "conversation_id": conversation.id,
        "status": conversation.status,
    }


@app.get("/conversations")
def list_conversations(db: Session = Depends(get_db)):
    rows = db.query(Conversation).order_by(Conversation.started_at.desc()).all()
    return [
        {
            "id": row.id,
            "chat_id": row.external_chat_id,
            "cliente": row.contact_name,
            "vendedor": row.seller_name,
            "canal": row.channel,
            "iniciada_em": row.started_at.isoformat() if row.started_at else None,
            "iniciada_por": row.started_by,
            "origem": row.origin,
            "status": row.status,
            "tempo_primeira_resposta_seg": row.response_time_seconds,
            "ultima_mensagem": row.last_message,
        }
        for row in rows
    ]
