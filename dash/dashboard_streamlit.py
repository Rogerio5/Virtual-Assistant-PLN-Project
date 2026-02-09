# dashboard_streamlit.py
# -*- coding: utf-8 -*-
"""
Dashboard Streamlit para Feedbacks (versão final)
- Conexão PostgreSQL via SQLAlchemy
- Filtros por data e usuário
- Upload de logo
- Gráficos (distribuição, por usuário, por tempo)
- Exportação PDF (Unicode) e CSV
- Uso de fonte DejaVu Sans para suporte a Unicode no PDF
- Tipagem e casts para reduzir avisos do Pylance
"""

import os
import tempfile
import datetime as dt
from typing import Optional, List, Any, cast

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import matplotlib as mpl
from matplotlib.figure import Figure
import streamlit as st
import requests
from sqlalchemy import create_engine
from fpdf import FPDF

# -------------------------------
# Configurações iniciais
# -------------------------------
st.set_page_config(page_title="Dashboard de Feedbacks", layout="wide")
sns.set_theme(style="darkgrid", palette="deep", font_scale=1.05)
mpl.rcParams["font.family"] = "DejaVu Sans"

# -------------------------------
# Localização da fonte DejaVu (para PDF Unicode)
# -------------------------------
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
DEJAVU_FILENAME = "DejaVuSans.ttf"
DEJAVU_PATH: Optional[str] = os.path.join(HERE, DEJAVU_FILENAME)
if not (DEJAVU_PATH and os.path.exists(DEJAVU_PATH)):
    try:
        from matplotlib import font_manager as fm
        candidates = fm.findSystemFonts()
        dejavu_candidates = [str(f) for f in candidates if "DejaVuSans" in os.path.basename(str(f))]
        DEJAVU_PATH = dejavu_candidates[0] if dejavu_candidates else None
    except Exception:
        DEJAVU_PATH = None

# -------------------------------
# Configuração da conexão (ajuste conforme seu ambiente)
# -------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:Engenharia10@localhost:5432/assistant_db",
)

# -------------------------------
# Utilitários
# -------------------------------
def prepare_datetime_column(df: pd.DataFrame, col: str = "created_at") -> pd.DataFrame:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def _normalize_note_value(n_raw: Any) -> Any:
    """
    Normaliza o índice 'nota' vindo de uma Series:
    - Se for inteiro (ou numpy integer) retorna int
    - Se for conversível para número inteiro retorna int
    - Caso contrário retorna a representação em string
    """
    # Tipos numéricos diretos
    if isinstance(n_raw, (int, np.integer)):
        return int(n_raw)
    # floats (inclui numpy.float64)
    if isinstance(n_raw, (float, np.floating)):
        if float(n_raw).is_integer():
            return int(n_raw)
        return int(n_raw)
    # strings e outros: tentar converter com segurança
    try:
        # tenta converter strings numéricas como "4" ou "4.0"
        n_float = float(n_raw)
        if float(n_float).is_integer():
            return int(n_float)
        return int(n_float)
    except Exception:
        # fallback para string
        return str(n_raw)

def _normalize_proportion(p_raw: Any) -> float:
    """
    Normaliza o valor de proporção para float com fallback 0.0.
    """
    try:
        return float(p_raw)
    except Exception:
        return 0.0

# -------------------------------
# Carregamento de dados (cacheado)
# -------------------------------
@st.cache_data(ttl=10)
def carregar_feedbacks() -> pd.DataFrame:
    try:
        engine = create_engine(DATABASE_URL)
        df = pd.read_sql("SELECT * FROM feedbacks;", con=engine)
    except Exception:
        df = pd.DataFrame(columns=["id", "user_id", "rating", "comment", "created_at"])
    df = prepare_datetime_column(df, "created_at")
    return df

# -------------------------------
# Gráficos
# -------------------------------
def fig_vazia(mensagem: str) -> Figure:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.text(0.5, 0.5, mensagem, ha="center", va="center", fontsize=12)
    ax.set_xticks([])
    ax.set_yticks([])
    plt.tight_layout()
    return fig

def fig_distribuicao_notas(df: pd.DataFrame) -> Figure:
    if df.empty or "rating" not in df.columns:
        return fig_vazia("Sem dados")
    counts = df["rating"].dropna().astype(int).value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(x=counts.index.astype(str), y=counts.values, palette="viridis", ax=ax)
    ax.set_title("Distribuição das notas")
    ax.set_xlabel("Nota")
    ax.set_ylabel("Quantidade")
    total = int(counts.sum()) if counts.size > 0 else 0
    for p in ax.patches:
        if isinstance(p, Rectangle):
            p_rect = cast(Rectangle, p)
            height = p_rect.get_height()
            x = p_rect.get_x()
            width = p_rect.get_width()
            perc = (height / total * 100) if total > 0 else 0.0
            ax.annotate(
                f"{int(height)}\n{perc:.1f}%",
                (x + width / 2, height),
                ha="center",
                va="bottom",
                fontsize=9,
            )
    plt.tight_layout()
    return fig

def fig_feedbacks_por_usuario(df: pd.DataFrame, top_n: int = 10) -> Figure:
    if df.empty or "user_id" not in df.columns:
        return fig_vazia("Sem dados")
    counts = df["user_id"].astype(str).value_counts().nlargest(top_n)
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(x=counts.index.astype(str), y=counts.values, palette="magma", ax=ax)
    ax.set_title(f"Feedbacks por usuário (Top {top_n})")
    ax.set_xlabel("")
    ax.set_ylabel("Quantidade")
    plt.xticks(rotation=45, ha="right")
    total = int(counts.sum()) if counts.size > 0 else 0
    for p in ax.patches:
        if isinstance(p, Rectangle):
            p_rect = cast(Rectangle, p)
            height = p_rect.get_height()
            x = p_rect.get_x()
            width = p_rect.get_width()
            perc = (height / total * 100) if total > 0 else 0.0
            ax.annotate(
                f"{int(height)} ({perc:.1f}%)",
                (x + width / 2, height),
                ha="center",
                va="bottom",
                fontsize=9,
            )
    plt.tight_layout()
    return fig

def fig_feedbacks_tempo(df: pd.DataFrame) -> Figure:
    if df.empty or "created_at" not in df.columns:
        return fig_vazia("Sem dados")
    df_t = df.copy()
    df_t["dia"] = pd.to_datetime(df_t["created_at"]).dt.date
    serie = df_t.groupby("dia").size().reset_index(name="total")
    fig, ax = plt.subplots(figsize=(8, 4))
    if not serie.empty:
        ax.plot(pd.to_datetime(serie["dia"]), serie["total"], marker="o", color="#1f77b4")
    ax.set_title("Feedbacks ao longo do tempo")
    ax.set_xlabel("Data")
    ax.set_ylabel("Quantidade")
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig

# -------------------------------
# Salvar figura temporária (retorna caminho)
# -------------------------------
def salvar_fig_temp(fig: Figure, nome: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png", prefix=f"{nome}_")
    fig.savefig(tmp.name, format="png", bbox_inches="tight")
    tmp.close()
    return tmp.name

# -------------------------------
# PDF Unicode (DejaVu) - retorna bytes
# -------------------------------
class PDFUnicode(FPDF):
    def __init__(self, dejavu_path: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dejavu_path = dejavu_path
        if self._dejavu_path and os.path.exists(self._dejavu_path):
            try:
                self.add_font("DejaVu", "", self._dejavu_path, uni=True)
                self.add_font("DejaVu", "B", self._dejavu_path, uni=True)
            except Exception:
                pass

    def footer(self):
        self.set_y(-15)
        try:
            self.set_font("DejaVu", "", 10)
        except Exception:
            self.set_font("Helvetica", "", 10)
        self.set_text_color(100, 100, 100)
        data = dt.datetime.now().strftime("%d/%m/%Y")
        self.cell(0, 10, f"Criado em: {data} | Página {self.page_no()}", align="C")

def gerar_relatorio_pdf_bytes(df_filtrado: pd.DataFrame) -> bytes:
    total = len(df_filtrado)
    media = float(df_filtrado["rating"].mean()) if "rating" in df_filtrado.columns and not df_filtrado.empty else 0.0
    usuarios = int(df_filtrado["user_id"].nunique()) if "user_id" in df_filtrado.columns and not df_filtrado.empty else 0

    periodo = ""
    if "created_at" in df_filtrado.columns and not df_filtrado.empty:
        inicio = pd.to_datetime(df_filtrado["created_at"]).min().date()
        fim = pd.to_datetime(df_filtrado["created_at"]).max().date()
        periodo = f"{inicio} até {fim}"

    dist = df_filtrado["rating"].value_counts(normalize=True).sort_index() if "rating" in df_filtrado.columns else pd.Series(dtype=float)

    # Construir texto de distribuição de forma segura para evitar avisos de tipo
    dist_text_lines: List[str] = []
    for n_raw, p_raw in dist.items():
        n_int_or_str = _normalize_note_value(n_raw)
        p_float = _normalize_proportion(p_raw)
        dist_text_lines.append(f"Nota {n_int_or_str} - {p_float * 100:.1f}% dos feedbacks")

    dist_texto = "\n".join(dist_text_lines)

    figs_paths: List[str] = []
    try:
        f1 = fig_distribuicao_notas(df_filtrado)
        p1 = salvar_fig_temp(f1, "notas")
        figs_paths.append(p1)
    except Exception:
        pass
    try:
        f2 = fig_feedbacks_por_usuario(df_filtrado)
        p2 = salvar_fig_temp(f2, "usuarios")
        figs_paths.append(p2)
    except Exception:
        pass
    try:
        f3 = fig_feedbacks_tempo(df_filtrado)
        p3 = salvar_fig_temp(f3, "tempo")
        figs_paths.append(p3)
    except Exception:
        pass

    pdf = PDFUnicode(dejavu_path=DEJAVU_PATH)
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()
    try:
        pdf.set_font("DejaVu", "B", 20)
    except Exception:
        pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "Empresa: Sabino Tech AI", ln=True, align="C")
    try:
        pdf.set_font("DejaVu", "", 12)
    except Exception:
        pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, "Gerado por: Rogério", ln=True, align="C")
    pdf.cell(0, 8, dt.datetime.now().strftime("%d/%m/%Y"), ln=True, align="C")

    pdf.add_page()
    try:
        pdf.set_font("DejaVu", "B", 16)
    except Exception:
        pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Relatório de Feedbacks", ln=True, align="C")
    pdf.ln(6)
    try:
        pdf.set_font("DejaVu", "", 11)
    except Exception:
        pdf.set_font("Helvetica", "", 11)
    resumo_text = f"Total de feedbacks: {total}\nMédia das notas: {media:.2f}\nUsuários únicos: {usuarios}\nPeríodo analisado: {periodo}\n\n{dist_texto}"
    pdf.multi_cell(0, 7, resumo_text)

    if figs_paths:
        pdf.add_page()
        try:
            pdf.set_font("DejaVu", "B", 14)
        except Exception:
            pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Gráficos", ln=True, align="C")
        y = 30
        try:
            if len(figs_paths) >= 1:
                pdf.image(figs_paths[0], x=10, y=y, w=90)
            if len(figs_paths) >= 2:
                pdf.image(figs_paths[1], x=110, y=y, w=90)
            if len(figs_paths) >= 3:
                pdf.image(figs_paths[2], x=10, y=y + 90, w=180)
        except Exception:
            pass

    out = pdf.output(dest="S")
    if isinstance(out, str):
        pdf_bytes = out.encode("latin-1", errors="ignore")
    else:
        pdf_bytes = bytes(out)

    for p in figs_paths:
        try:
            os.remove(p)
        except Exception:
            pass

    return pdf_bytes

# -------------------------------
# Interface Streamlit
# -------------------------------
def main():
    st.title("📊 Dashboard de Feedbacks")
    st.markdown("Visualização interativa dos feedbacks armazenados no banco")

    # -------------------------------
    # Autenticação via sidebar (requests.Session)
    # -------------------------------
    if "session" not in st.session_state:
        st.session_state.session = requests.Session()
        st.session_state.authenticated = False
        st.session_state.user = None

    def do_login(username: str, password: str) -> None:
        s = st.session_state.session
        try:
            res = s.post(f"{os.getenv('API_BASE_URL', 'http://localhost:8000')}/auth/login",
                         json={"username": username, "password": password}, timeout=10)
            if res.ok:
                st.session_state.authenticated = True
                st.session_state.user = username
                st.success("Logado com sucesso")
            else:
                st.error("Credenciais inválidas")
        except Exception as e:
            st.error(f"Erro ao conectar: {e}")

    def do_logout() -> None:
        s = st.session_state.session
        try:
            s.post(f"{os.getenv('API_BASE_URL', 'http://localhost:8000')}/auth/logout", timeout=5)
        finally:
            st.session_state.authenticated = False
            st.session_state.user = None
            st.success("Desconectado")

    # Barra lateral de autenticação (aparece acima dos filtros)
    with st.sidebar:
        st.header("Acesso")
        if not st.session_state.authenticated:
            username = st.text_input("Usuário", key="login_user")
            password = st.text_input("Senha", type="password", key="login_pass")
            if st.button("Entrar"):
                do_login(username, password)
            st.markdown("---")
            st.info("Faça login para acessar o assistente de voz e o dashboard.")
        else:
            st.markdown(f"**Usuário:** {st.session_state.user}")
            if st.button("Sair"):
                do_logout()

    # Bloqueio do conteúdo principal se não autenticado
    if not st.session_state.authenticated:
        st.warning("Faça login na barra lateral para acessar o dashboard e o assistente de voz.")
        st.stop()

    # -------------------------------
    # Carregar dados e filtros
    # -------------------------------
    df = carregar_feedbacks()

    st.sidebar.header("🔎 Filtros")
    if df.empty:
        st.sidebar.info("Sem dados no banco.")
        min_date = dt.date.today()
        max_date = dt.date.today()
    else:
        df = prepare_datetime_column(df, "created_at")
        min_date = pd.to_datetime(df["created_at"]).min().date()
        max_date = pd.to_datetime(df["created_at"]).max().date()

    data_inicio = st.sidebar.date_input("Data inicial", value=min_date, min_value=min_date, max_value=max_date, key="data_inicio")
    data_fim = st.sidebar.date_input("Data final", value=max_date, min_value=min_date, max_value=max_date, key="data_fim")
    if data_inicio > data_fim:
        st.sidebar.error("Data inicial não pode ser maior que a data final")
        data_inicio, data_fim = data_fim, data_inicio

    start_dt = pd.to_datetime(dt.datetime.combine(data_inicio, dt.time.min))
    end_dt = pd.to_datetime(dt.datetime.combine(data_fim, dt.time.max))

    if not df.empty and pd.api.types.is_datetime64_any_dtype(df["created_at"]):
        df_filtrado = df[df["created_at"].between(start_dt, end_dt)].copy()
    else:
        df_filtrado = df.copy()

    usuario_options = ["Todos"] + sorted([str(u) for u in df["user_id"].dropna().unique().tolist()]) if "user_id" in df.columns else ["Todos"]
    usuario = st.sidebar.selectbox("Filtrar por usuário", options=usuario_options, index=0, key="usuario")
    if usuario != "Todos":
        df_filtrado = df_filtrado[df_filtrado["user_id"].astype(str) == str(usuario)].copy()

    # construir opções de nota de forma segura e tipada (todas strings para o selectbox)
    if "rating" in df.columns:
        rating_series = pd.to_numeric(df["rating"], errors="coerce").dropna().astype(int)
        rating_vals: List[int] = sorted({int(x) for x in rating_series})
        rating_options: List[str] = ["Todas"] + [str(x) for x in rating_vals]
    else:
        rating_options = ["Todas"]

    nota_selecionada: str = st.sidebar.selectbox("Filtrar por nota", options=rating_options, index=0, key="nota")
    if nota_selecionada != "Todas":
        try:
            nota_int = int(nota_selecionada)
            df_filtrado = df_filtrado[df_filtrado["rating"].astype(int) == nota_int].copy()
        except Exception:
            pass

    logo_file = st.sidebar.file_uploader("Enviar logo para marca d'água (PNG/JPG)", type=["png", "jpg", "jpeg"], key="logo")
    if logo_file is not None:
        st.sidebar.image(logo_file, caption="Logo carregada", use_column_width=True)

    st.subheader("Visualizações")
    if df_filtrado.empty:
        st.info("Sem dados para exibir com os filtros aplicados.")
    else:
        cols = st.columns(2)
        with cols[0]:
            st.markdown("**Distribuição das notas**")
            st.pyplot(fig_distribuicao_notas(df_filtrado))
        with cols[1]:
            st.markdown("**Feedbacks por usuário (Top 10)**")
            st.pyplot(fig_feedbacks_por_usuario(df_filtrado, top_n=10))

        st.subheader("Evolução temporal")
        st.pyplot(fig_feedbacks_tempo(df_filtrado))

    st.subheader("Tabela detalhada de feedbacks")
    if df_filtrado.empty:
        st.info("Sem dados para exibir.")
    else:
        df_show = df_filtrado[["id", "user_id", "rating", "comment", "created_at"]].copy()
        st.dataframe(df_show, use_container_width=True)

    st.sidebar.header("📥 Exportar")
    if not df_filtrado.empty:
        csv_bytes = df_filtrado.to_csv(index=False).encode("utf-8")
        st.sidebar.download_button("Baixar dados (CSV)", data=csv_bytes, file_name="feedbacks.csv", mime="text/csv", key="download_csv")
    else:
        st.sidebar.write("CSV: sem dados")

    if st.sidebar.button("Gerar relatório PDF"):
        if df_filtrado.empty:
            st.sidebar.info("Sem dados para gerar relatório.")
        else:
            with st.spinner("Gerando PDF..."):
                try:
                    pdf_bytes = gerar_relatorio_pdf_bytes(df_filtrado)
                    st.sidebar.success("PDF gerado.")
                    st.sidebar.download_button("Baixar relatório (PDF)", data=pdf_bytes, file_name="relatorio_feedbacks.pdf", mime="application/pdf", key="download_pdf")
                except Exception as e:
                    st.sidebar.error(f"Erro ao gerar PDF: {e}")

if __name__ == "__main__":
    main()
