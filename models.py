from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    external_chat_id = Column(String(120), unique=True, index=True, nullable=False)
    contact_name = Column(String(255), default="Sem nome")
    seller_name = Column(String(255), default="Não atribuído")
    channel = Column(String(100), default="Desconhecido")
    started_at = Column(DateTime, nullable=True)
    started_by = Column(String(50), default="desconhecido")
    origin = Column(String(50), default="desconhecido")
    first_response_at = Column(DateTime, nullable=True)
    response_time_seconds = Column(Integer, nullable=True)
    last_message = Column(Text, nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="Aguardando resposta")

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    external_message_id = Column(String(120), index=True, nullable=True)
    author_type = Column(String(50), default="desconhecido")
    author_name = Column(String(255), default="Desconhecido")
    message_text = Column(Text, default="")
    sent_at = Column(DateTime, nullable=True)

    conversation = relationship("Conversation", back_populates="messages")
