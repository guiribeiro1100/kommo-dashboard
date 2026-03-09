import os
import pandas as pd
import requests
import streamlit as st
from io import BytesIO

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Kommo Conversas", page_icon="💬", layout="wide")
st.title("💬 Relatório de Conversas Iniciadas")
st.caption("Painel inicial para acompanhar conversas do Kommo por vendedor")

@st.cache_data(ttl=15)
def load_data() -> pd.DataFrame:
    response = requests.get(f"{API_URL}/conversations", timeout=10)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)
    if df.empty:
        return df

    df["iniciada_em"] = pd.to_datetime(df["iniciada_em"])
    df["tempo_primeira_resposta_min"] = (df["tempo_primeira_resposta_seg"] / 60).round(1)
    return df

try:
    df = load_data()
except Exception as exc:
    st.error(f"Não consegui falar com a API: {exc}")
    st.stop()

if df.empty:
    st.warning("Ainda não há conversas salvas.")
    st.stop()

with st.sidebar:
    st.header("Filtros")
    vendedores = ["Todos"] + sorted(df["vendedor"].dropna().unique().tolist())
    canais = ["Todos"] + sorted(df["canal"].dropna().unique().tolist())
    status_opts = ["Todos"] + sorted(df["status"].dropna().unique().tolist())

    vendedor = st.selectbox("Vendedor", vendedores)
    canal = st.selectbox("Canal", canais)
    status = st.selectbox("Status", status_opts)

filtered = df.copy()
if vendedor != "Todos":
    filtered = filtered[filtered["vendedor"] == vendedor]
if canal != "Todos":
    filtered = filtered[filtered["canal"] == canal]
if status != "Todos":
    filtered = filtered[filtered["status"] == status]

respondidas = filtered[filtered["status"].isin(["Respondida", "Cliente respondeu"])]
media_resp = respondidas["tempo_primeira_resposta_min"].dropna().mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Conversas iniciadas", int(len(filtered)))
col2.metric("Respondidas", int((filtered["status"] == "Respondida").sum()))
col3.metric("Aguardando resposta", int((filtered["status"] == "Aguardando resposta").sum()))
col4.metric("Tempo médio 1ª resposta", f"{media_resp:.1f} min" if pd.notna(media_resp) else "—")

st.subheader("Lista de conversas")
show = filtered[[
    "cliente", "vendedor", "canal", "iniciada_em", "iniciada_por",
    "origem", "status", "tempo_primeira_resposta_min", "ultima_mensagem"
]].rename(columns={
    "cliente": "Cliente",
    "vendedor": "Vendedor",
    "canal": "Canal",
    "iniciada_em": "Iniciada em",
    "iniciada_por": "Iniciada por",
    "origem": "Origem",
    "status": "Status",
    "tempo_primeira_resposta_min": "Tempo 1ª resposta (min)",
    "ultima_mensagem": "Última mensagem",
})

st.dataframe(show.sort_values("Iniciada em", ascending=False), use_container_width=True, hide_index=True)

st.subheader("Ranking por vendedor")
ranking = (
    filtered.groupby("vendedor", dropna=False)
    .size()
    .reset_index(name="Conversas iniciadas")
    .rename(columns={"vendedor": "Vendedor"})
    .sort_values("Conversas iniciadas", ascending=False)
)
st.dataframe(ranking, use_container_width=True, hide_index=True)

excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    show.to_excel(writer, index=False, sheet_name="Conversas")
    ranking.to_excel(writer, index=False, sheet_name="Ranking")
excel_buffer.seek(0)

st.download_button(
    "📥 Baixar relatório em Excel",
    data=excel_buffer,
    file_name="relatorio_conversas_kommo.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
