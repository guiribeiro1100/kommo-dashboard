# Kommo Conversas - projeto inicial

Esse projeto é um MVP para você acompanhar **todas as conversas iniciadas** por vendedor.

## O que ele faz
- recebe eventos de mensagem por webhook
- salva as conversas em banco SQLite
- calcula quem iniciou a conversa
- calcula tempo de primeira resposta
- mostra um painel em Streamlit
- exporta relatório para Excel

## Estrutura
- `api.py` → API FastAPI para receber webhook e listar conversas
- `streamlit_app.py` → painel visual
- `models.py` → tabelas do banco
- `service.py` → regras da conversa
- `schemas.py` → modelo do payload
- `database.py` → conexão com banco

## 1) Instalar
```bash
pip install -r requirements.txt
```

## 2) Configurar ambiente
Copie `.env.example` para `.env`.

Se quiser testar sem validar assinatura do Kommo, coloque:
```env
WEBHOOK_SECRET=desabilitar
```

## 3) Rodar a API
```bash
uvicorn api:app --reload
```

## 4) Rodar o painel
Em outro terminal:
```bash
streamlit run streamlit_app.py
```

## 5) Testar o webhook manualmente
Com a API ligada, envie esse exemplo:

```bash
curl -X POST http://127.0.0.1:8000/webhook/kommo \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "chat-100",
    "message_id": "m-100",
    "contact_name": "Frigorífico Exemplo",
    "seller_name": "Carlos",
    "channel": "WhatsApp",
    "author_type": "cliente",
    "author_name": "Ricardo",
    "message_text": "Quero saber o preço.",
    "sent_at": "2026-03-09T14:00:00"
  }'
```

## Como plugar no Kommo de verdade
Você vai precisar:
1. criar uma integração privada
2. configurar OAuth ou token compatível
3. cadastrar o webhook da sua API
4. adaptar o payload real do Kommo para o formato esperado em `schemas.py`
5. manter a validação de assinatura via `X-Signature`

## Sobre o Kommo
A documentação oficial mostra que:
- integrações podem ser privadas ou públicas
- webhooks podem ser configurados na conta
- Chats API tem endpoints para conversas, histórico e webhooks
- webhooks de chat usam cabeçalho `X-Signature`

## Próximo passo recomendado
Depois que esse MVP estiver rodando, o próximo ajuste é eu adaptar o `api.py` para o **payload exato da sua conta Kommo**.
