from fastapi import FastAPI, Depends, Request, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import hashlib
import hmac
import os
from datetime import datetime

from database import Base, engine, SessionLocal
from models import Conversation

app = FastAPI(title="Kommo Conversas API")


# cria tabelas
Base.metadata.create_all(bind=engine)


# conexão com banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# chave do webhook
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


def validate_signature(body: bytes, signature: str | None) -> bool:

    if not WEBHOOK_SECRET:
        return True

    if not signature:
        return False

    digest = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha1
    ).hexdigest()

    return hmac.compare_digest(digest, signature)


# rota raiz
@app.get("/")
def root():
    return {"status": "API rodando"}


# webhook kommo
@app.post("/webhook/kommo")
async def receive_kommo_webhook(
    request: Request,
    x_signature: str | None = Header(None),
    db: Session = Depends(get_db)
):

    raw_body = await request.body()

    if not validate_signature(raw_body, x_signature):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    data = await request.json()

    chat_id = data.get("chat_id")
    contact_name = data.get("contact_name")
    seller_name = data.get("seller_name")
    channel = data.get("channel")
    message_text = data.get("message_text")
    author_type = data.get("author_type")
    sent_at = data.get("sent_at")

    if sent_at:
        sent_at = datetime.fromisoformat(sent_at)

    conversa = (
        db.query(Conversation)
        .filter(Conversation.chat_id == chat_id)
        .first()
    )

    if not conversa:

        conversa = Conversation(
            chat_id=chat_id,
            client_name=contact_name,
            seller_name=seller_name,
            channel=channel,
            started_at=sent_at,
            started_by=author_type,
            status="Aguardando resposta",
            last_message=message_text
        )

        db.add(conversa)
        db.commit()
        db.refresh(conversa)

    else:

        conversa.last_message = message_text

        if author_type == "vendedor":
            conversa.status = "Respondida"

        db.commit()

    return {
        "ok": True,
        "conversation_id": conversa.id,
        "status": conversa.status
    }


# lista de conversas
@app.get("/conversations")
def list_conversations(db: Session = Depends(get_db)):

    conversas = db.query(Conversation).all()

    resposta = []

    for c in conversas:
        resposta.append({
            "id": c.id,
            "chat_id": c.chat_id,
            "cliente": c.client_name,
            "vendedor": c.seller_name,
            "canal": c.channel,
            "iniciada_em": c.started_at,
            "iniciada_por": c.started_by,
            "status": c.status,
            "ultima_mensagem": c.last_message
        })

    return resposta


# relatório conversas iniciadas por vendedor
@app.get("/report/conversas-iniciadas")
def report_conversas_iniciadas(db: Session = Depends(get_db)):

    resultados = (
        db.query(
            Conversation.seller_name,
            func.count(Conversation.id).label("conversas_iniciadas")
        )
        .filter(Conversation.started_by == "vendedor")
        .group_by(Conversation.seller_name)
        .all()
    )

    resposta = []

    for r in resultados:
        resposta.append({
            "vendedor": r.seller_name,
            "conversas_iniciadas": r.conversas_iniciadas
        })

    return resposta