from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class WebhookMessage(BaseModel):
    chat_id: str
    message_id: Optional[str] = None
    contact_name: Optional[str] = "Sem nome"
    seller_name: Optional[str] = "Não atribuído"
    channel: Optional[str] = "Desconhecido"
    author_type: str
    author_name: Optional[str] = "Desconhecido"
    message_text: Optional[str] = ""
    sent_at: datetime
