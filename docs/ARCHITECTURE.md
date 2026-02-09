
---

## 🏗️ `ARCHITECTURE.md`

```markdown
# 🏗️ Arquitetura do Projeto - Assistente Virtual PLN

Este documento descreve a arquitetura geral do sistema.

---

## 🔎 Visão Geral
O projeto é composto por quatro principais componentes:

- **Backend (FastAPI)**: processa comandos, reconhecimento de voz, síntese de fala e coleta feedbacks.
- **Frontend (React)**: interface web para interação com o assistente.
- **Dashboard (Streamlit)**: visualização e relatórios dos feedbacks.
- **Banco de Dados (PostgreSQL)**: armazenamento persistente dos feedbacks.

---

## 🔄 Fluxo de Dados
1. Usuário interage via frontend (texto ou áudio).
2. Backend processa entrada (NLP, voz, comandos).
3. Feedbacks são salvos no banco PostgreSQL.
4. Dashboard consome dados do banco e gera relatórios interativos e em PDF/Excel.

---

## 📊 Diagrama Simplificado
[Frontend React] ---> [Backend FastAPI] ---> [Postgres DB] ---> [Dashboard Streamlit]

---

## ⚙️ Tecnologias Utilizadas
- **Backend**: FastAPI, SQLAlchemy, Alembic, spaCy, scikit-learn
- **Frontend**: React, Axios, Cypress
- **Dashboard**: Streamlit, Seaborn, Matplotlib, FPDF
- **Banco**: PostgreSQL
- **Infraestrutura**: Docker, Docker Compose


# 📊 Diagrama ASCII da Arquitetura

+-------------------+        +-------------------+        +-------------------+
|                   |        |                   |        |                   |
|   Frontend        | -----> |   Backend         | -----> |   Banco de Dados  |
|   (React / Vite)  |        |   (FastAPI)       |        |   (PostgreSQL)    |
|                   |        |                   |        |                   |
+-------------------+        +-------------------+        +-------------------+
        |                                                        ^
        |                                                        |
        v                                                        |
+-------------------+                                            |
|                   |                                            |
|   Dashboard       | -------------------------------------------+
|   (Streamlit)     |
|                   |
+-------------------+

Fluxo:
1. Usuário interage via Frontend (texto ou áudio).
2. Backend processa entrada (NLP, Whisper, TTS, comandos).
3. Feedbacks e dados são persistidos no Banco de Dados.
4. Dashboard consome dados do Banco e gera relatórios interativos.


# 🔄 Fluxo de Requisição

Usuário (Texto/Áudio)
        |
        v
+-------------------+
|   Frontend React  |
|   (UI / Browser)  |
+-------------------+
        |
        v
+-------------------+
|   Backend FastAPI |
|   Endpoints:      |
|   - /assistant    |
|   - /feedback     |
|   - /auth         |
+-------------------+
        |
        +-----------------------------+
        |                             |
        v                             v
+-------------------+        +-------------------+
| Speech-to-Text    |        | NLP Pipeline      |
| (Whisper)         |        | (Intents/Entities)|
+-------------------+        +-------------------+
        |                             |
        v                             v
+-------------------+        +-------------------+
| ChatGPT (opcional)|        | Command Executor  |
+-------------------+        +-------------------+
        |
        v
+-------------------+
| Text-to-Speech    |
| (gTTS / pyttsx3)  |
+-------------------+
        |
        v
Resposta (Texto + Áudio)
        |
        v
+-------------------+
|   Frontend React  |
|   Exibe resposta  |
|   Reproduz áudio  |
+-------------------+

Feedbacks → Banco de Dados (PostgreSQL) → Dashboard (Streamlit)

# 📝 Fluxo de Feedbacks

Usuário envia feedback (mensagem + rating)
        |
        v
+-------------------+
|   Frontend React  |
|   Formulário UI   |
+-------------------+
        |
        v
+-------------------+
|   Backend FastAPI |
|   Endpoint:       |
|   - /feedback     |
+-------------------+
        |
        v
+-------------------+
| Feedback Manager  |
| - Salva no banco  |
| - Ou fallback     |
|   em arquivo JSON |
+-------------------+
        |
        v
+-------------------+
| Banco de Dados    |
| (PostgreSQL)      |
+-------------------+
        |
        v
+-------------------+
| Dashboard         |
| (Streamlit)       |
| - Relatórios PDF  |
| - Visualizações   |
+-------------------+

Fluxo:
1. Usuário envia feedback via frontend.
2. Backend recebe e valida entrada.
3. Feedback Manager salva no banco (ou fallback local).
4. Dashboard consome dados e gera relatórios.
