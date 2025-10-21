import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import math

# ========== CONFIG ==========

SUPABASE_URL = "DB_HOST"
SUPABASE_KEY = "DB_KEY"

AUTO_REFRESH_MS = 60000  # 60s (silencioso, sem contador)
PAGE_TITLE = "📊 Painel Supervisório — Operação de Call Center"

# ========== CONEXÃO ==========
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title=PAGE_TITLE, layout="wide")
st.markdown(f"### {PAGE_TITLE}")

# Auto-refresh silencioso via JS (sem for/sleep na tela)
st.components.v1.html(
    f"""<script>
        setTimeout(function() {{ window.parent.location.reload(); }}, {AUTO_REFRESH_MS});
    </script>""",
    height=0,
)

# ========== FUNÇÕES ==========
@st.cache_data(ttl=50)
def carregar_ultima_linha():
    """
    Busca apenas a última linha pela coluna 'created_at' (mais recente).
    Ajuste o nome da coluna se no seu banco for diferente (ex.: 'CREATE AT' -> 'created_at').
    """
    resp = (
        supabase
        .table("operacao_rpo")
        .select("*")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    dados = resp.data or []
    return dados[0] if len(dados) else None

def fmt_int(x):
    try:
        return f"{int(x):,}".replace(",", ".")
    except Exception:
        return "-"

def fmt_float(x, casas=2):
    try:
        if x is None or (isinstance(x, float) and (math.isnan(x))):
            return "-"
        return f"{float(x):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "-"

def fmt_moeda_brl(x):
    v = fmt_float(x, 2)
    return f"R$ {v}" if v != "-" else "-"

def fmt_datetime_br(dt_str):
    if not dt_str:
        return "-"
    try:
        # Pandas lida bem com timestamptz do Supabase
        ts = pd.to_datetime(dt_str, utc=True).tz_convert("America/Sao_Paulo")
        return ts.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(dt_str)

# ========== BUSCA DADO MAIS RECENTE ==========
row = carregar_ultima_linha()

if not row:
    st.warning("Nenhum dado encontrado na tabela **operacao_rpo**.")
    st.stop()

# Mapear campos do banco -> KPIs
status_campanhas   = row.get("st_campanhas_rpo")
qtde_mailing       = row.get("qtde_mailing_rpo")
ticket_medio       = row.get("ticket_medio_rpo")
qtde_leads         = row.get("qtde_lead_rpo")
qtde_chamadas      = row.get("qtde_chamadas_rpo")
ultimo_lead        = row.get("ultimo_lead_rpo")            # esperado string/datetime
valor_consumido    = row.get("valor_consumido_rpo")
created_at         = row.get("created_at")                 # timestamptz gerado pelo Supabase

# ========== TOPO / STATUS ==========
col_head1, col_head2 = st.columns([2, 1])
with col_head1:
    st.caption("")
with col_head2:
    st.markdown(
        f"""
        <div style="
            background:#eef6ff;border:1px solid #cfe5ff;padding:10px 12px;
            border-radius:10px;text-align:center;">
            <div style="font-size:12px;color:#355;">
                Atualizado em :
            </div>
            <div style="font-size:15px;font-weight:600;">
                {fmt_datetime_br(created_at)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ========== KPIs EM CARDS ==========
# Linha 1
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Status Campanhas", status_campanhas if status_campanhas else "-")
with c2:
    st.metric("Mailing (Qtde)", fmt_int(qtde_mailing))
with c3:
    st.metric("Ticket Médio", fmt_moeda_brl(ticket_medio))
with c4:
    st.metric("Leads (Qtde)", fmt_int(qtde_leads))

# Linha 2
c5, c6, c7, c8 = st.columns(4)
with c5:
    st.metric("Chamadas (Qtde)", fmt_int(qtde_chamadas))
with c6:
    st.metric("Valor Consumido", fmt_moeda_brl(valor_consumido))
with c7:
    st.metric("Último Lead (hora)", fmt_datetime_br(ultimo_lead))
#with c8:
    #st.metric("created_at (DB)", fmt_datetime_br(created_at))

# Rodapé discreto
st.caption("Atualização a cada 60s")

