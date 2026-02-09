# -*- coding: utf-8 -*-
"""
dashboard.py — Streamlit dashboard multilíngue para feedbacks
- Conexão PostgreSQL
- Filtros por data e usuário
- Upload de logo
- Gráficos (distribuição, pizza, por usuário, por tempo)
- Tabela
- Exportação PDF (Unicode) e CSV na barra lateral
- Seleção de idioma e tema
"""

import os
import io
import locale
import datetime
from typing import Optional, Any, Dict, Callable, cast

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib import font_manager as fm
import streamlit as st
from sqlalchemy import create_engine
from fpdf import FPDF

# Optional: Arabic shaping & bidi
try:
    import arabic_reshaper  # type: ignore
    from bidi.algorithm import get_display  # type: ignore
    _HAS_ARABIC_LIBS = True
except Exception:
    _HAS_ARABIC_LIBS = False

# -------------------------------
# Streamlit page config (call before other st.*)
# -------------------------------
st.set_page_config(page_title="Dashboard de Feedbacks", layout="wide")

# -------------------------------
# Visual settings and constants
# -------------------------------
sns.set_theme(style="darkgrid", palette="deep", font_scale=1.05)
try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except Exception:
    pass

TOP_USERS_DISPLAY = 10
PDF_PAGE_WIDTH = 210  # mm (A4)
PDF_PAGE_HEIGHT = 297  # mm (A4)
PDF_MARGIN = 10  # mm
API_URL = "http://localhost:8000/feedbacks"  # fallback API (se necessário)

# -------------------------------
# Font handling (Unicode)
# -------------------------------
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
DEJAVU_FILENAME = "DejaVuSans.ttf"
DEJAVU_PATH: Optional[str] = os.path.join(HERE, DEJAVU_FILENAME)

if not (DEJAVU_PATH and os.path.exists(DEJAVU_PATH)):
    try:
        candidates = fm.findSystemFonts()
        dejavu_candidates = [str(f) for f in candidates if "DejaVuSans" in os.path.basename(str(f))]
        DEJAVU_PATH = dejavu_candidates[0] if dejavu_candidates else None
    except Exception:
        DEJAVU_PATH = None

if DEJAVU_PATH and os.path.exists(DEJAVU_PATH):
    try:
        fm.fontManager.addfont(DEJAVU_PATH)
        mpl.rcParams["font.family"] = "DejaVu Sans"
    except Exception:
        pass
else:
    mpl.rcParams["font.family"] = "DejaVu Sans"

# -------------------------------
# Text utilities
# -------------------------------
def prepare_text(text: Optional[Any], lang: str = "pt") -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    if lang == "ar" and _HAS_ARABIC_LIBS:
        try:
            reshaped = arabic_reshaper.reshape(text)
            bidi_text = str(get_display(reshaped))
            return bidi_text
        except Exception:
            return text
    return text

# -------------------------------
# Translations (mantém todos os idiomas)
# -------------------------------
textos: Dict[str, Dict[str, str]] = {
    "pt": {
        "titulo": "📊 Dashboard de Feedbacks",
        "conexao_ok": "Conexão com o banco estabelecida!",
        "filtros_gerais": "Filtros gerais",
        "data_inicial": "Data inicial",
        "data_final": "Data final",
        "filtrar_usuario": "Filtrar por usuário",
        "info_gerais": "ℹ️ Informações gerais",
        "total_feedbacks": "Total de feedbacks",
        "media_notas": "Média das notas",
        "usuarios_unicos": "Usuários únicos",
        "periodo_analisado": "Período analisado",
        "alertas": "Alertas automáticos",
        "media_baixa": "⚠️ Atenção: A média das notas está baixa",
        "atividade_intensa": "🚨 Usuários com atividade intensa detectados:",
        "grafico_tema": "📌 Escolha o tema do gráfico",
        "grafico_notas": "📊 Distribuição das notas",
        "grafico_usuarios": "👤 Feedbacks por usuário",
        "grafico_tempo": "⏳ Feedbacks ao longo do tempo",
        "grafico_pizza": "🥧 Análise percentual das notas",
        "exportar_pdf": "📄 Exportar relatório (PDF)",
        "sem_dados": "Sem dados para exibir",
        "capa_empresa": "Empresa: Sabino Tech AI",
        "capa_autor": "Gerado por Rogério",
        "tabela_feedbacks": "Tabela detalhada de feedbacks",
        "nota": "Nota",
        "quantidade": "Quantidade",
        "data": "Data",
        "total": "Total",
        "evolucao_temporal": "Evolução temporal",
        "distribuicao_notas": "Distribuição das notas",
        "pizza_notas": "Análise percentual das notas (pizza)",
        "feedbacks_por_usuario_top": "Feedbacks por usuário (Top)",
        "visualizacoes": "Visualizações",
        "escolha_visualizacoes": "Escolha as visualizações a exibir",
        "selecionadas": "Visualizações selecionadas",
        "selecione_uma": "Selecione ao menos uma visualização na barra lateral.",
        "pdf_capa_titulo": "Relatório de Feedbacks",
        "pdf_capa_subtitulo": "Período",
        "pdf_secao_resumo": "Resumo",
        "pdf_secao_graficos": "Gráficos",
        "pdf_secao_tabela": "Tabela de feedbacks",
        "pdf_gerado": "Relatório PDF gerado com sucesso!"
    },
    "en": {
        "titulo": "📊 Feedback Dashboard",
        "conexao_ok": "Database connection established!",
        "filtros_gerais": "General filters",
        "data_inicial": "Start date",
        "data_final": "End date",
        "filtrar_usuario": "Filter by user",
        "info_gerais": "ℹ️ General information",
        "total_feedbacks": "Total feedbacks",
        "media_notas": "Average rating",
        "usuarios_unicos": "Unique users",
        "periodo_analisado": "Analyzed period",
        "alertas": "Automatic alerts",
        "media_baixa": "⚠️ Warning: Average rating is low",
        "atividade_intensa": "🚨 Users with intense activity detected:",
        "grafico_tema": "📌 Choose chart theme",
        "grafico_notas": "📊 Rating distribution",
        "grafico_usuarios": "👤 Feedbacks by user",
        "grafico_tempo": "⏳ Feedbacks over time",
        "grafico_pizza": "🥧 Percentage analysis of ratings",
        "exportar_pdf": "📄 Export report (PDF)",
        "sem_dados": "No data to display",
        "capa_empresa": "Company: Sabino Tech AI",
        "capa_autor": "Generated by Rogério",
        "tabela_feedbacks": "Detailed feedbacks table",
        "nota": "Rating",
        "quantidade": "Count",
        "data": "Date",
        "total": "Total",
        "evolucao_temporal": "Temporal evolution",
        "distribuicao_notas": "Rating distribution",
        "pizza_notas": "Percentage analysis of ratings (pie)",
        "feedbacks_por_usuario_top": "Feedbacks by user (Top)",
        "visualizacoes": "Visualizations",
        "escolha_visualizacoes": "Choose visualizations to display",
        "selecionadas": "Selected visualizations",
        "selecione_uma": "Select at least one visualization in the sidebar.",
        "pdf_capa_titulo": "Feedback Report",
        "pdf_capa_subtitulo": "Period",
        "pdf_secao_resumo": "Summary",
        "pdf_secao_graficos": "Charts",
        "pdf_secao_tabela": "Feedbacks table",
        "pdf_gerado": "PDF report generated successfully!"
    },
    "es": {
        "titulo": "📊 Panel de Retroalimentaciones",
        "conexao_ok": "¡Conexión con la base de datos establecida!",
        "filtros_gerais": "Filtros generales",
        "data_inicial": "Fecha inicial",
        "data_final": "Fecha final",
        "filtrar_usuario": "Filtrar por usuario",
        "info_gerais": "ℹ️ Información general",
        "total_feedbacks": "Total de retroalimentaciones",
        "media_notas": "Promedio de calificaciones",
        "usuarios_unicos": "Usuarios únicos",
        "periodo_analisado": "Período analizado",
        "alertas": "Alertas automáticas",
        "media_baixa": "⚠️ Atención: El promedio de calificaciones es bajo",
        "atividade_intensa": "🚨 Usuarios con actividad intensa detectados:",
        "grafico_tema": "📌 Elegir tema del gráfico",
        "grafico_notas": "📊 Distribución de calificaciones",
        "grafico_usuarios": "👤 Retroalimentaciones por usuario",
        "grafico_tempo": "⏳ Retroalimentaciones a lo largo del tiempo",
        "grafico_pizza": "🥧 Análisis porcentual de calificaciones",
        "exportar_pdf": "📄 Exportar informe (PDF)",
        "sem_dados": "Sin datos para mostrar",
        "capa_empresa": "Empresa: Sabino Tech AI",
        "capa_autor": "Generado por Rogério",
        "tabela_feedbacks": "Tabla detallada de retroalimentaciones",
        "nota": "Calificación",
        "quantidade": "Cantidad",
        "data": "Fecha",
        "total": "Total",
        "evolucao_temporal": "Evolución temporal",
        "distribuicao_notas": "Distribución de calificaciones",
        "pizza_notas": "Análisis porcentual de calificaciones (torta)",
        "feedbacks_por_usuario_top": "Retroalimentaciones por usuario (Top)",
        "visualizacoes": "Visualizaciones",
        "escolha_visualizacoes": "Elige las visualizaciones a mostrar",
        "selecionadas": "Visualizaciones seleccionadas",
        "selecione_uma": "Selecciona al menos una visualización en la barra lateral.",
        "pdf_capa_titulo": "Informe de Retroalimentaciones",
        "pdf_capa_subtitulo": "Período",
        "pdf_secao_resumo": "Resumen",
        "pdf_secao_graficos": "Gráficos",
        "pdf_secao_tabela": "Tabla de retroalimentaciones",
        "pdf_gerado": "¡Informe PDF generado con éxito!"
    },
    "fr": {
        "titulo": "📊 Tableau de bord des retours",
        "conexao_ok": "Connexion à la base de données établie !",
        "filtros_gerais": "Filtres généraux",
        "data_inicial": "Date de début",
        "data_final": "Date de fin",
        "filtrar_usuario": "Filtrer par utilisateur",
        "info_gerais": "ℹ️ Informations générales",
        "total_feedbacks": "Total des retours",
        "media_notas": "Note moyenne",
        "usuarios_unicos": "Utilisateurs uniques",
        "periodo_analisado": "Période analysée",
        "alertas": "Alertes automatiques",
        "media_baixa": "⚠️ Attention : la note moyenne est basse",
        "atividade_intensa": "🚨 Utilisateurs à activité intense détectés :",
        "grafico_tema": "📌 Choisir le thème du graphique",
        "grafico_notas": "📊 Répartition des notes",
        "grafico_usuarios": "👤 Retours par utilisateur",
        "grafico_tempo": "⏳ Retours dans le temps",
        "grafico_pizza": "🥧 Analyse en pourcentage des notes",
        "exportar_pdf": "📄 Exporter le rapport (PDF)",
        "sem_dados": "Aucune donnée à afficher",
        "capa_empresa": "Entreprise : Sabino Tech AI",
        "capa_autor": "Généré par Rogério",
        "tabela_feedbacks": "Tableau détaillé des retours",
        "nota": "Note",
        "quantidade": "Quantité",
        "data": "Date",
        "total": "Total",
        "evolucao_temporal": "Évolution temporelle",
        "distribuicao_notas": "Répartition des notes",
        "pizza_notas": "Analyse en pourcentage des notes (camembert)",
        "feedbacks_por_usuario_top": "Retours par utilisateur (Top)",
        "visualizacoes": "Visualisations",
        "escolha_visualizacoes": "Choisissez les visualisations à afficher",
        "selecionadas": "Visualisations sélectionnées",
        "selecione_uma": "Sélectionnez au moins une visualisation dans la barre latérale.",
        "pdf_capa_titulo": "Rapport de retours",
        "pdf_capa_subtitulo": "Période",
        "pdf_secao_resumo": "Résumé",
        "pdf_secao_graficos": "Graphiques",
        "pdf_secao_tabela": "Tableau des retours",
        "pdf_gerado": "Rapport PDF généré avec succès !"
    },
    "de": {
        "titulo": "📊 Feedback-Dashboard",
        "conexao_ok": "Datenbankverbindung hergestellt!",
        "filtros_gerais": "Allgemeine Filter",
        "data_inicial": "Startdatum",
        "data_final": "Enddatum",
        "filtrar_usuario": "Nach Benutzer filtern",
        "info_gerais": "ℹ️ Allgemeine Informationen",
        "total_feedbacks": "Gesamtanzahl Feedbacks",
        "media_notas": "Durchschnittsbewertung",
        "usuarios_unicos": "Eindeutige Benutzer",
        "periodo_analisado": "Analysierter Zeitraum",
        "alertas": "Automatische Warnungen",
        "media_baixa": "⚠️ Achtung: Die Durchschnittsbewertung ist niedrig",
        "atividade_intensa": "🚨 Benutzer mit intensiver Aktivität erkannt:",
        "grafico_tema": "📌 Diagrammthema wählen",
        "grafico_notas": "📊 Verteilung der Bewertungen",
        "grafico_usuarios": "👤 Feedbacks pro Benutzer",
        "grafico_tempo": "⏳ Feedbacks im Zeitverlauf",
        "grafico_pizza": "🥧 Prozentuale Analyse der Bewertungen",
        "exportar_pdf": "📄 Bericht exportieren (PDF)",
        "sem_dados": "Keine Daten zum Anzeigen",
        "capa_empresa": "Unternehmen: Sabino Tech AI",
        "capa_autor": "Erstellt von Rogério",
        "tabela_feedbacks": "Detaillierte Feedback-Tabelle",
        "nota": "Bewertung",
        "quantidade": "Menge",
        "data": "Datum",
        "total": "Gesamt",
        "evolucao_temporal": "Zeitliche Entwicklung",
        "distribuicao_notas": "Verteilung der Bewertungen",
        "pizza_notas": "Prozentuale Analyse der Bewertungen (Torte)",
        "feedbacks_por_usuario_top": "Feedbacks pro Benutzer (Top)",
        "visualizacoes": "Visualisierungen",
        "escolha_visualizacoes": "Wählen Sie die anzuzeigenden Visualisierungen",
        "selecionadas": "Ausgewählte Visualisierungen",
        "selecione_uma": "Wählen Sie mindestens eine Visualisierung in der Seitenleiste.",
        "pdf_capa_titulo": "Feedback-Bericht",
        "pdf_capa_subtitulo": "Zeitraum",
        "pdf_secao_resumo": "Zusammenfassung",
        "pdf_secao_graficos": "Diagramme",
        "pdf_secao_tabela": "Feedback-Tabelle",
        "pdf_gerado": "PDF-Bericht erfolgreich erstellt!"
    },
    "ru": {
        "titulo": "📊 Панель обратной связи",
        "conexao_ok": "Подключение к базе данных установлено!",
        "filtros_gerais": "Общие фильтры",
        "data_inicial": "Дата начала",
        "data_final": "Дата окончания",
        "filtrar_usuario": "Фильтр по пользователю",
        "info_gerais": "ℹ️ Общая информация",
        "total_feedbacks": "Всего отзывов",
        "media_notas": "Средняя оценка",
        "usuarios_unicos": "Уникальные пользователи",
        "periodo_analisado": "Анализируемый период",
        "alertas": "Автоматические предупреждения",
        "media_baixa": "⚠️ Внимание: низкая средняя оценка",
        "atividade_intensa": "🚨 Обнаружены пользователи с высокой активностью:",
        "grafico_tema": "📌 Выберите тему графика",
        "grafico_notas": "📊 Распределение оценок",
        "grafico_usuarios": "👤 Отзывы по пользователям",
        "grafico_tempo": "⏳ Отзывы во времени",
        "grafico_pizza": "🥧 Процентный анализ оценок",
        "exportar_pdf": "📄 Экспорт отчёта (PDF)",
        "sem_dados": "Нет данных для отображения",
        "capa_empresa": "Компания: Sabino Tech AI",
        "capa_autor": "Сгенерировано Rogério",
        "tabela_feedbacks": "Подробная таблица отзывов",
        "nota": "Оценка",
        "quantidade": "Количество",
        "data": "Дата",
        "total": "Итого",
        "evolucao_temporal": "Динамика во времени",
        "distribuicao_notas": "Распределение оценок",
        "pizza_notas": "Процентный анализ оценок (круговая диаграмма)",
        "feedbacks_por_usuario_top": "Отзывы по пользователям (Топ)",
        "visualizacoes": "Визуализации",
        "escolha_visualizacoes": "Выберите визуализации для отображения",
        "selecionadas": "Выбранные визуализации",
        "selecione_uma": "Выберите хотя бы одну визуализацию в боковой панели.",
        "pdf_capa_titulo": "Отчёт по отзывам",
        "pdf_capa_subtitulo": "Период",
        "pdf_secao_resumo": "Резюме",
        "pdf_secao_graficos": "Графики",
        "pdf_secao_tabela": "Таблица отзывов",
        "pdf_gerado": "PDF-отчёт успешно создан!"
    },
    "ar": {
        "titulo": "📊 لوحة تعليقات",
        "conexao_ok": "تم إنشاء اتصال قاعدة البيانات!",
        "filtros_gerais": "عوامل التصفية العامة",
        "data_inicial": "تاريخ البدء",
        "data_final": "تاريخ الانتهاء",
        "filtrar_usuario": "تصفية حسب المستخدم",
        "info_gerais": "ℹ️ معلومات عامة",
        "total_feedbacks": "إجمالي التعليقات",
        "media_notas": "متوسط التقييم",
        "usuarios_unicos": "المستخدمون الفريدون",
        "periodo_analisado": "الفترة المحللة",
        "alertas": "تنبيهات تلقائية",
        "media_baixa": "⚠️ تحذير: متوسط التقييم منخفض",
        "atividade_intensa": "🚨 تم اكتشاف مستخدمين ذوي نشاط مكثف:",
        "grafico_tema": "📌 اختر سمة المخطط",
        "grafico_notas": "📊 توزيع التقييمات",
        "grafico_usuarios": "👤 التعليقات حسب المستخدم",
        "grafico_tempo": "⏳ التعليقات عبر الزمن",
        "grafico_pizza": "🥧 تحليل النسب المئوية للتقييمات",
        "exportar_pdf": "📄 تصدير التقرير (PDF)",
        "sem_dados": "لا توجد بيانات للعرض",
        "capa_empresa": "الشركة: Sabino Tech AI",
        "capa_autor": "تم إنشاؤه بواسطة Rogério",
        "tabela_feedbacks": "جدول التعليقات التفصيلي",
        "nota": "تقييم",
        "quantidade": "الكمية",
        "data": "التاريخ",
        "total": "الإجمالي",
        "evolucao_temporal": "التطور الزمني",
        "distribuicao_notas": "توزيع التقييمات",
        "pizza_notas": "تحليل النسب المئوية للتقييمات (فطيرة)",
        "feedbacks_por_usuario_top": "التعليقات حسب المستخدم (الأعلى)",
        "visualizacoes": "المرئيات",
        "escolha_visualizacoes": "اختر المرئيات للعرض",
        "selecionadas": "المرئيات المختارة",
        "selecione_uma": "اختر مرئية واحدة على الأقل من الشريط الجانبي.",
        "pdf_capa_titulo": "تقرير التعليقات",
        "pdf_capa_subtitulo": "الفترة",
        "pdf_secao_resumo": "ملخص",
        "pdf_secao_graficos": "مخططات",
        "pdf_secao_tabela": "جدول التعليقات",
        "pdf_gerado": "تم إنشاء تقرير PDF بنجاح!"
    },
    "it": {
        "titulo": "📊 Dashboard dei feedback",
        "conexao_ok": "Connessione al database stabilita!",
        "filtros_gerais": "Filtri generali",
        "data_inicial": "Data iniziale",
        "data_final": "Data finale",
        "filtrar_usuario": "Filtra per utente",
        "info_gerais": "ℹ️ Informazioni generali",
        "total_feedbacks": "Totale feedback",
        "media_notas": "Valutazione media",
        "usuarios_unicos": "Utenti unici",
        "periodo_analisado": "Periodo analizzato",
        "alertas": "Avvisi automatici",
        "media_baixa": "⚠️ Attenzione: la valutazione media è bassa",
        "atividade_intensa": "🚨 Rilevati utenti con attività intensa:",
        "grafico_tema": "📌 Scegli il tema del grafico",
        "grafico_notas": "📊 Distribuzione delle valutazioni",
        "grafico_usuarios": "👤 Feedback per utente",
        "grafico_tempo": "⏳ Feedback nel tempo",
        "grafico_pizza": "🥧 Analisi percentuale delle valutazioni",
        "exportar_pdf": "📄 Esporta rapporto (PDF)",
        "sem_dados": "Nessun dato da visualizzare",
        "capa_empresa": "Azienda: Sabino Tech AI",
        "capa_autor": "Generato da Rogério",
        "tabela_feedbacks": "Tabella dettagliata dei feedback",
        "nota": "Valutazione",
        "quantidade": "Quantità",
        "data": "Data",
        "total": "Totale",
        "evolucao_temporal": "Evoluzione temporale",
        "distribuicao_notas": "Distribuzione delle valutazioni",
        "pizza_notas": "Analisi percentuale delle valutazioni (torta)",
        "feedbacks_por_usuario_top": "Feedback per utente (Top)",
        "visualizacoes": "Visualizzazioni",
        "escolha_visualizacoes": "Scegli le visualizzazioni da mostrare",
        "selecionadas": "Visualizzazioni selezionate",
        "selecione_uma": "Seleziona almeno una visualizzazione nella barra laterale.",
        "pdf_capa_titulo": "Rapporto sui feedback",
        "pdf_capa_subtitulo": "Periodo",
        "pdf_secao_resumo": "Riepilogo",
        "pdf_secao_graficos": "Grafici",
        "pdf_secao_tabela": "Tabella dei feedback",
        "pdf_gerado": "Rapporto PDF generato con successo!"
    }
}

# -------------------------------
# Language selector (apenas uma vez)
# -------------------------------
idioma = st.sidebar.selectbox(
    "🌐 Idioma / Language",
    ["Português", "English", "Español", "Français", "Deutsch", "Русский", "العربية", "Italiano"],
    key="idioma"
)

lang_map = {
    "Português": "pt",
    "English": "en",
    "Español": "es",
    "Français": "fr",
    "Deutsch": "de",
    "Русский": "ru",
    "العربية": "ar",
    "Italiano": "it",
}

lang = lang_map.get(idioma, "pt")
t = textos.get(lang, textos["pt"])

# -------------------------------
# Title (apenas uma vez)
# -------------------------------
st.title(prepare_text(t["titulo"], lang))

# -------------------------------
# Database connection (robusto)
# -------------------------------
try:
    engine = create_engine("postgresql+psycopg2://postgres:Engenharia10@localhost:5432/assistant_db")
    df = pd.read_sql("SELECT * FROM feedbacks;", engine)

    expected_cols = {"id", "user_id", "rating", "comment", "created_at"}
    for col in expected_cols:
        if col not in df.columns:
            df[col] = pd.NA

    # Conversão segura para datetime
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.dropna(subset=["created_at"]).copy()
    try:
        df["created_at"] = df["created_at"].dt.tz_localize(None)
    except Exception:
        pass
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    st.success(prepare_text(t["conexao_ok"], lang))
except Exception as e:
    st.error(prepare_text(str(e), lang))
    st.stop()

# -------------------------------
# Filters (robusto e sem .dt.date direto)
# -------------------------------
st.sidebar.header(prepare_text(t["filtros_gerais"], lang))

if df.empty:
    min_date = datetime.date.today()
    max_date = datetime.date.today()
else:
    min_date = df["created_at"].min().date()
    max_date = df["created_at"].max().date()

data_inicio = st.sidebar.date_input(
    prepare_text(t["data_inicial"], lang),
    value=min_date,
    min_value=min_date,
    max_value=max_date,
    key="data_inicio"
)
data_fim = st.sidebar.date_input(
    prepare_text(t["data_final"], lang),
    value=max_date,
    min_value=min_date,
    max_value=max_date,
    key="data_fim"
)

if data_inicio > data_fim:
    st.sidebar.error(prepare_text("Data inicial não pode ser maior que a data final", lang))
    data_inicio, data_fim = data_fim, data_inicio

start_dt = pd.to_datetime(datetime.datetime.combine(data_inicio, datetime.time.min))
end_dt = pd.to_datetime(datetime.datetime.combine(data_fim, datetime.time.max))

if not df.empty and pd.api.types.is_datetime64_any_dtype(df["created_at"]):
    df_filtrado = df[df["created_at"].between(start_dt, end_dt)].copy()
else:
    df_filtrado = df.copy()

usuario_options = ["Todos"] + sorted([str(u) for u in df["user_id"].dropna().unique().tolist()])
usuario_selecionado = st.sidebar.selectbox(
    prepare_text(t["filtrar_usuario"], lang),
    usuario_options,
    index=0,
    key="usuario"
)
if usuario_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["user_id"].astype(str) == str(usuario_selecionado)].copy()

# -------------------------------
# Logo uploader
# -------------------------------
logo_file = st.sidebar.file_uploader(
    prepare_text("Enviar logo para marca d'água (PNG/JPG)", lang),
    type=["png", "jpg", "jpeg"],
    key="logo"
)
if logo_file is not None:
    st.sidebar.image(logo_file, caption=prepare_text("Logo carregada", lang), use_column_width=True)

# -------------------------------
# Sidebar: chart theme selection
# -------------------------------
st.sidebar.subheader(prepare_text(t["grafico_tema"], lang))
tema = st.sidebar.selectbox(
    prepare_text(t["grafico_tema"], lang),
    ["deep", "muted", "pastel", "dark", "colorblind", "viridis", "magma"],
    key="tema"
)
try:
    if tema in ["deep", "muted", "pastel", "dark", "colorblind"]:
        sns.set_theme(style="darkgrid", palette=tema, font_scale=1.05)
    else:
        sns.set_theme(style="darkgrid", font_scale=1.05)
except Exception:
    pass

# -------------------------------
# General info display
# -------------------------------
st.subheader(prepare_text(t["info_gerais"], lang))
total_feedbacks = len(df_filtrado)
rating_vals_all = np.asarray(df_filtrado["rating"].dropna().astype(float).values) if "rating" in df_filtrado.columns else np.array([], dtype=float)
media_notas = float(np.mean(rating_vals_all)) if rating_vals_all.size > 0 else 0.0
usuarios_unicos = int(df_filtrado["user_id"].nunique()) if not df_filtrado.empty else 0

st.write(f"{prepare_text(t['total_feedbacks'], lang)}: **{total_feedbacks}**")
st.write(f"{prepare_text(t['media_notas'], lang)}: **{media_notas:.2f}**")
st.write(f"{prepare_text(t['usuarios_unicos'], lang)}: **{usuarios_unicos}**")
st.write(f"{prepare_text(t['periodo_analisado'], lang)}: **{data_inicio} até {data_fim}**")

# -------------------------------
# Alerts
# -------------------------------
st.subheader(prepare_text(t["alertas"], lang))
if total_feedbacks == 0:
    st.info(prepare_text(t["sem_dados"], lang))
else:
    if media_notas < 3:
        st.error(f"{prepare_text(t['media_baixa'], lang)} ({media_notas:.2f})")

    df_alerta = df_filtrado.copy()
    df_alerta["dia"] = df_alerta["created_at"].dt.date
    feedbacks_por_usuario_dia = df_alerta.groupby(["user_id", "dia"]).size().reset_index(name="total")
    usuarios_intensos = feedbacks_por_usuario_dia[feedbacks_por_usuario_dia["total"] > 5]

    if not usuarios_intensos.empty:
        st.warning(prepare_text(t["atividade_intensa"], lang))
        for _, row in usuarios_intensos.iterrows():
            st.write(f"**{row['user_id']}** → {row['total']} feedbacks em {row['dia']}")

# -------------------------------
# Plot functions
# -------------------------------
def fig_vazia(mensagem: str) -> Figure:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.text(0.5, 0.5, mensagem, ha="center", va="center", fontsize=12)
    ax.set_xticks([])
    ax.set_yticks([])
    plt.tight_layout()
    return fig

def fig_distribuicao_notas(dataframe: pd.DataFrame) -> Figure:
    if dataframe.empty or "rating" not in dataframe.columns:
        return fig_vazia(prepare_text(t["sem_dados"], lang))
    counts = dataframe["rating"].dropna().astype(float).round().value_counts().sort_index()
    counts_values = np.asarray(counts.values, dtype=float)
    total = int(np.sum(counts_values)) if counts_values.size > 0 else 0
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(x=counts.index.astype(str), y=counts_values, palette="viridis", ax=ax)
    ax.set_title(prepare_text(t["grafico_notas"], lang))
    ax.set_xlabel(prepare_text(t.get("nota", "Nota"), lang))
    ax.set_ylabel(prepare_text(t.get("quantidade", "Quantidade"), lang))
    for p in ax.patches:
        if isinstance(p, Rectangle):
            height = p.get_height()
            x = p.get_x()
            width = p.get_width()
            if total > 0:
                perc = height / total * 100
                ax.annotate(prepare_text(f"{int(height)}\n{perc:.1f}%", lang),
                            (x + width / 2, height),
                            ha="center", va="bottom", fontsize=9, color="black")
    rating_vals = np.asarray(dataframe["rating"].dropna().astype(float).values)
    media = float(np.mean(rating_vals)) if rating_vals.size > 0 else 0.0
    resumo = prepare_text(f"Total: {total}\nMédia: {media:.2f}", lang)
    ax.text(1.02, 0.5, resumo, transform=ax.transAxes, fontsize=10,
            verticalalignment='center', bbox=dict(boxstyle="round,pad=0.5", facecolor="#f0f0f0", edgecolor="#cccccc"))
    plt.tight_layout()
    return fig

def fig_feedbacks_por_usuario(dataframe: pd.DataFrame, top_n: int = TOP_USERS_DISPLAY) -> Figure:
    if dataframe.empty or "user_id" not in dataframe.columns:
        return fig_vazia(prepare_text(t["sem_dados"], lang))
    counts = dataframe["user_id"].astype(str).value_counts().nlargest(top_n)
    counts_values = np.asarray(counts.values, dtype=float)
    total = int(np.sum(counts_values)) if counts_values.size > 0 else 0
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(x=counts.index.astype(str), y=counts_values, palette="magma", ax=ax)
    ax.set_title(prepare_text(f"{t['grafico_usuarios']} (Top {top_n})", lang))
    ax.set_xlabel("")
    ax.set_ylabel(prepare_text(t.get("quantidade", "Quantidade"), lang))
    plt.xticks(rotation=45, ha="right")
    for p in ax.patches:
        if isinstance(p, Rectangle):
            height = p.get_height()
            x = p.get_x()
            width = p.get_width()
            perc = (height / total * 100) if total > 0 else 0
            ax.annotate(prepare_text(f"{int(height)} ({perc:.1f}%)", lang),
                        (x + width / 2, height),
                        ha="center", va="bottom", fontsize=9, color="black")
    top_user = counts.idxmax() if not counts.empty else "N/A"
    top_count = int(counts.max()) if not counts.empty else 0
    legenda = prepare_text(f"Total feedbacks: {total}\nUsuário mais ativo: {top_user} ({top_count})", lang)
    ax.text(1.02, 0.5, legenda, transform=ax.transAxes, fontsize=10,
            verticalalignment='center', bbox=dict(boxstyle="round,pad=0.5", facecolor="#f9f9f9", edgecolor="#dddddd"))
    plt.tight_layout()
    return fig

def fig_feedbacks_tempo(dataframe: pd.DataFrame) -> Figure:
    if dataframe.empty or "created_at" not in dataframe.columns:
        return fig_vazia(prepare_text(t["sem_dados"], lang))
    df_t = dataframe.copy()
    df_t["dia"] = df_t["created_at"].dt.date
    serie = df_t.groupby("dia").size().reset_index(name="total")
    fig, ax = plt.subplots(figsize=(8, 4))
    if not serie.empty:
        ax.plot(pd.to_datetime(serie["dia"]), serie["total"], marker="o", color="#1f77b4")
    ax.set_title(prepare_text(t["grafico_tempo"], lang))
    ax.set_xlabel(prepare_text(t.get("data", "Data"), lang))
    ax.set_ylabel(prepare_text(t.get("quantidade", "Quantidade"), lang))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
    ax.grid(True, alpha=0.3)
    totals = np.asarray(serie["total"].values, dtype=float) if not serie.empty else np.array([], dtype=float)
    total = int(np.sum(totals)) if totals.size > 0 else 0
    media_dia = float(np.mean(totals)) if totals.size > 0 else 0.0
    legenda = prepare_text(f"Total: {total}\nMédia/dia: {media_dia:.2f}", lang)
    ax.text(1.02, 0.5, legenda, transform=ax.transAxes, fontsize=10,
            verticalalignment='center', bbox=dict(boxstyle="round,pad=0.5", facecolor="#f0f0f0", edgecolor="#cccccc"))
    plt.tight_layout()
    return fig

def fig_pizza_notas(dataframe: pd.DataFrame) -> Figure:
    if dataframe.empty or "rating" not in dataframe.columns:
        return fig_vazia(prepare_text(t["sem_dados"], lang))
    counts = dataframe["rating"].dropna().astype(float).round().value_counts().sort_index()
    if counts.empty:
        return fig_vazia(prepare_text(t["sem_dados"], lang))
    labels = [prepare_text(f"Nota {int(k)}", lang) for k in counts.index.tolist()]
    values = np.asarray(counts.values, dtype=float)
    fig, ax = plt.subplots(figsize=(6, 4))
    pie_result = ax.pie(values.tolist(), labels=labels, autopct=lambda p: f"{p:.1f}%", startangle=90)
    ax.axis("equal")
    ax.set_title(prepare_text(t["grafico_pizza"], lang))
    total = int(np.sum(values)) if values.size > 0 else 0
    legenda = "\n".join([f"{lab}: {int(cnt)} ({(cnt/total*100 if total>0 else 0):.1f}%)" for lab, cnt in zip(labels, values)])
    ax.text(1.02, 0.5, prepare_text(legenda, lang), transform=ax.transAxes, fontsize=10,
            verticalalignment="center", bbox=dict(boxstyle="round,pad=0.5", facecolor="#ffffff", edgecolor="#dddddd"))
    plt.tight_layout()
    return fig

# -------------------------------
# Visualization multi-select and display
# -------------------------------
st.subheader(prepare_text(t["visualizacoes"], lang))
st.write(prepare_text(t["escolha_visualizacoes"], lang))

vis_options: Dict[str, Callable[[pd.DataFrame], Figure]] = {
    prepare_text(t["distribuicao_notas"], lang): fig_distribuicao_notas,
    prepare_text(t["pizza_notas"], lang): fig_pizza_notas,
    prepare_text(t["feedbacks_por_usuario_top"], lang): lambda df_: fig_feedbacks_por_usuario(df_, TOP_USERS_DISPLAY),
    prepare_text(t["evolucao_temporal"], lang): fig_feedbacks_tempo,
}
selecionados = st.sidebar.multiselect(
    prepare_text(t["escolha_visualizacoes"], lang),
    options=list(vis_options.keys()),
    default=[prepare_text(t["distribuicao_notas"], lang), prepare_text(t["pizza_notas"], lang)],
    key="vis_selecionadas"
)

st.subheader(prepare_text(t["selecionadas"], lang))
if not selecionados:
    st.info(prepare_text(t["selecione_uma"], lang))
else:
    cols = st.columns(2)
    idx = 0
    for key in selecionados:
        func = vis_options.get(key)
        if callable(func):
            try:
                fig = cast(Figure, func(df_filtrado))
            except Exception:
                fig = fig_vazia(prepare_text(t["sem_dados"], lang))
        else:
            fig = fig_vazia(prepare_text(t["sem_dados"], lang))

        col = cols[idx % 2]
        with col:
            st.markdown(f"**{key}**")
            st.pyplot(fig)
        idx += 1

# -------------------------------
# Table display
# -------------------------------
st.subheader(prepare_text(t["tabela_feedbacks"], lang))
if df_filtrado.empty:
    st.info(prepare_text(t["sem_dados"], lang))
else:
    df_show = df_filtrado[["id", "user_id", "rating", "comment", "created_at"]].copy()
    st.dataframe(df_show, use_container_width=True)

# -------------------------------
# Export PDF and CSV
# -------------------------------
class PDF(FPDF):
    def __init__(self, *args, dejavu_path: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._dejavu_path = dejavu_path
        if self._dejavu_path and os.path.exists(self._dejavu_path):
            try:
                # registra DejaVu como fonte Unicode
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
        data = datetime.datetime.now().strftime("%d/%m/%Y")
        self.cell(0, 10, f"Criado em: {data} | Página {self.page_no()}", align="C")

def export_pdf_bytes(dataframe: pd.DataFrame) -> bytes:
    pdf = PDF(unit="mm", format="A4", dejavu_path=DEJAVU_PATH)
    pdf.set_auto_page_break(auto=True, margin=PDF_MARGIN)

    # Capa
    try:
        pdf.set_font("DejaVu", "B", 24)
    except Exception:
        pdf.set_font("Helvetica", "B", 24)
    pdf.add_page()
    pdf.cell(0, 14, t["pdf_capa_titulo"], align="C", ln=True)

    try:
        pdf.set_font("DejaVu", "", 12)
    except Exception:
        pdf.set_font("Helvetica", "", 12)
    pdf.ln(6)
    pdf.cell(0, 8, t["capa_empresa"], align="C", ln=True)
    pdf.cell(0, 8, t["capa_autor"], align="C", ln=True)
    pdf.cell(0, 8, datetime.datetime.now().strftime("%d/%m/%Y"), align="C", ln=True)

    # Resumo
    pdf.add_page()
    try:
        pdf.set_font("DejaVu", "B", 16)
    except Exception:
        pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, t["pdf_secao_resumo"], ln=True)

    try:
        pdf.set_font("DejaVu", "", 12)
    except Exception:
        pdf.set_font("Helvetica", "", 12)

    total = len(dataframe)
    media = dataframe["rating"].mean() if not dataframe.empty else 0
    usuarios = dataframe["user_id"].nunique() if not dataframe.empty else 0

    pdf.cell(0, 8, f"{t['total_feedbacks']}: {total}", ln=True)
    pdf.cell(0, 8, f"{t['media_notas']}: {media:.2f}", ln=True)
    pdf.cell(0, 8, f"{t['usuarios_unicos']}: {usuarios}", ln=True)

    # Tabela
    pdf.add_page()
    try:
        pdf.set_font("DejaVu", "B", 14)
    except Exception:
        pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, t["pdf_secao_tabela"], ln=True)
    try:
        pdf.set_font("DejaVu", "", 9)
    except Exception:
        pdf.set_font("Helvetica", "", 9)

    cols = ["id", "user_id", "rating", "comment", "created_at"]
    df_tab = dataframe[cols].copy() if not dataframe.empty else pd.DataFrame(columns=cols)
    df_tab["created_at"] = df_tab["created_at"].astype(str)

    col_widths = [15, 45, 20, 80, 30]
    for _, row in df_tab.iterrows():
        cells = [
            str(row.get("id", "")),
            str(row.get("user_id", "")) if pd.notna(row.get("user_id", "")) else "",
            str(row.get("rating", "")),
            str(row.get("comment", ""))[:40] if pd.notna(row.get("comment", "")) else "",
            str(row.get("created_at", "")) if pd.notna(row.get("created_at", "")) else "",
        ]
        for i, cell in enumerate(cells):
            try:
                pdf.cell(int(col_widths[i]), int(6), str(cell), border=1)
            except Exception:
                safe = str(cell).encode("latin-1", errors="ignore").decode("latin-1", errors="ignore")
                pdf.cell(int(col_widths[i]), int(6), safe, border=1)
        pdf.ln(6)

    pdf_out: Any = pdf.output(dest="S")
    if isinstance(pdf_out, str):
        pdf_bytes = pdf_out.encode("latin-1", errors="ignore")
    elif isinstance(pdf_out, (bytes, bytearray)):
        pdf_bytes = bytes(pdf_out)
    else:
        pdf_bytes = str(pdf_out).encode("utf-8", errors="ignore")

    return pdf_bytes


def export_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    dataframe.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

# -------------------------------
# Streamlit UI: export buttons (usa df_filtrado atual)
# -------------------------------
def main():
    with st.sidebar:
        # Gerar PDF
        if st.button(t["exportar_pdf"], key="btn_pdf"):
            df_to_export = st.session_state.get("processed_df", df_filtrado)
            st.session_state["processed_df"] = df_to_export
            with st.spinner("Gerando PDF..."):
                try:
                    pdf_bytes = export_pdf_bytes(df_to_export)
                    st.session_state["last_pdf_bytes"] = pdf_bytes
                    st.success(t["pdf_gerado"])
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")

        if "last_pdf_bytes" in st.session_state:
            st.download_button(
                label="Baixar relatório (PDF)",
                data=st.session_state["last_pdf_bytes"],
                file_name="relatorio.pdf",
                mime="application/pdf",
                key="download_pdf"
            )

        st.markdown("---")

        # Gerar CSV
        if st.button("Gerar dados (CSV)", key="btn_csv"):
            df_to_export = st.session_state.get("processed_df", df_filtrado)
            st.session_state["processed_df"] = df_to_export
            with st.spinner("Gerando CSV..."):
                try:
                    csv_bytes = export_csv_bytes(df_to_export)
                    st.session_state["last_csv_bytes"] = csv_bytes
                    st.success("CSV gerado com sucesso.")
                except Exception as e:
                    st.error(f"Erro ao gerar CSV: {e}")

        if "last_csv_bytes" in st.session_state:
            st.download_button(
                label="Baixar dados (CSV)",
                data=st.session_state["last_csv_bytes"],
                file_name="dados.csv",
                mime="text/csv",
                key="download_csv"
            )

if __name__ == "__main__":
    main()
