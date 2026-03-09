from datetime import datetime
from sqlalchemy.orm import Session
from models import Conversation, Message
from schemas import WebhookMessage

CLIENT_LABELS = {"client", "cliente", "contact", "lead"}
SELLER_LABELS = {"seller", "vendedor", "manager", "user", "agent"}


def normalize_author(author_type: str) -> str:
    value = (author_type or "").strip().lower()
    if value in CLIENT_LABELS:
        return "cliente"
    if value in SELLER_LABELS:
        return "vendedor"
    return "desconhecido"


def upsert_message(db: Session, payload: WebhookMessage) -> Conversation:
    conversation = db.query(Conversation).filter_by(external_chat_id=payload.chat_id).first()

    author_type = normalize_author(payload.author_type)

    if not conversation:
        conversation = Conversation(
            external_chat_id=payload.chat_id,
            contact_name=payload.contact_name or "Sem nome",
            seller_name=payload.seller_name or "Não atribuído",
            channel=payload.channel or "Desconhecido",
            started_at=payload.sent_at,
            started_by=author_type,
            origin="Inbound" if author_type == "cliente" else "Outbound" if author_type == "vendedor" else "Desconhecido",
            last_message=payload.message_text or "",
            last_message_at=payload.sent_at,
            status="Aguardando resposta" if author_type == "cliente" else "Prospecção iniciada",
        )
        db.add(conversation)
        db.flush()
    else:
        if payload.contact_name:
            conversation.contact_name = payload.contact_name
        if payload.seller_name:
            conversation.seller_name = payload.seller_name
        if payload.channel:
            conversation.channel = payload.channel
        conversation.last_message = payload.message_text or conversation.last_message
        conversation.last_message_at = payload.sent_at

        if (
            conversation.started_by == "cliente"
            and author_type == "vendedor"
            and conversation.first_response_at is None
            and conversation.started_at is not None
        ):
            conversation.first_response_at = payload.sent_at
            delta = payload.sent_at - conversation.started_at
            conversation.response_time_seconds = max(int(delta.total_seconds()), 0)
            conversation.status = "Respondida"
        elif conversation.started_by == "vendedor" and author_type == "cliente":
            conversation.status = "Cliente respondeu"
        elif conversation.started_by == "cliente" and author_type == "cliente":
            conversation.status = "Aguardando resposta"

    message = Message(
        conversation_id=conversation.id,
        external_message_id=payload.message_id,
        author_type=author_type,
        author_name=payload.author_name or "Desconhecido",
        message_text=payload.message_text or "",
        sent_at=payload.sent_at,
    )
    db.add(message)
    db.commit()
    db.refresh(conversation)
    return conversation


def seed_demo_data(db: Session) -> None:
    if db.query(Conversation).count() > 0:
        return

    base_messages = [
        WebhookMessage(
            chat_id="chat-001",
            message_id="m-001",
            contact_name="Frigorífico Boa Carne",
            seller_name="Carlos",
            channel="WhatsApp",
            author_type="cliente",
            author_name="Marcos",
            message_text="Bom dia, queria orçamento.",
            sent_at=datetime(2026, 3, 9, 8, 40),
        ),
        WebhookMessage(
            chat_id="chat-001",
            message_id="m-002",
            contact_name="Frigorífico Boa Carne",
            seller_name="Carlos",
            channel="WhatsApp",
            author_type="vendedor",
            author_name="Carlos",
            message_text="Bom dia, consigo sim. Qual medida?",
            sent_at=datetime(2026, 3, 9, 8, 46),
        ),
        WebhookMessage(
            chat_id="chat-002",
            message_id="m-003",
            contact_name="Nordeste Foods",
            seller_name="Ana",
            channel="Instagram",
            author_type="vendedor",
            author_name="Ana",
            message_text="Olá, trabalhamos com discos de alta performance.",
            sent_at=datetime(2026, 3, 9, 9, 10),
        ),
        WebhookMessage(
            chat_id="chat-003",
            message_id="m-004",
            contact_name="Frigorífico Sertão Sul",
            seller_name="Pedro",
            channel="WhatsApp",
            author_type="cliente",
            author_name="João",
            message_text="Vocês atendem Bahia?",
            sent_at=datetime(2026, 3, 9, 10, 5),
        ),
    ]

    for item in base_messages:
        upsert_message(db, item)
