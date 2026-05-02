# 🤖 Virtual Assistant System — Repositório: Virtual-Assistant-PLN-Project

## 🧠 Sistema de Assistência Virtual com Processamento de Linguagem Natural (PLN)

Projeto em Construção !!

![Capa do Projeto - Assistente Virtual](assistente-virtual1.png)

---

## 🏅 Badges

- 📦 Tamanho do repositório:  
  ![GitHub repo size](https://img.shields.io/repo-size/Rogerio5/Virtual-Assistant-PLN-Project)

- 📄 Licença do projeto:  
  ![GitHub license](https://img.shields.io/github/license/Rogerio5/Virtual-Assistant-PLN-Project)

---

## 📋 Índice / Table of Contents (reduzido)

- [📖 Descrição / Description](#-descrição--description)  
- [⚙️ Funcionalidades / Features](#-funcionalidades--features)  
- [🚀 Execução / Execution](#-execução--execution)  
- [🌐 Acesso / Access](#-acesso--access)  
- [🧰 Tecnologias / Technologies](#-tecnologias--technologies)  
- [📊 Diagrama ASCII da Arquitetura](#-diagrama-ascii-da-arquitetura)  
- [🔄 Fluxo de Requisição](#-fluxo-de-requisição)
- [📝 Fluxo de Feedbacks](#-fluxo-de-Feedbacks)
- [⚙️ Configuração do backend/config.py](#-configuração-do-backendconfigpy)  
- [👨‍💻 Desenvolvedor / Developer](#-desenvolvedor--developer)  
- [📜 Licença / License](#-licença--license)


---

## 📖 Descrição / Description

**PT:**  
Este projeto tem como objetivo desenvolver um sistema de assistência virtual inteligente, utilizando técnicas de Processamento de Linguagem Natural (PLN). O assistente é capaz de compreender comandos em linguagem natural, responder perguntas, executar ações básicas e interagir com o usuário de forma contextual.

O sistema foi construído do zero com base nas bibliotecas estudadas durante o curso, e cumpre os seguintes requisitos:

✅ Compreensão de linguagem natural  
✅ Geração de respostas automáticas  
✅ Reconhecimento de intenções e entidades  
✅ Execução de comandos simples (ex: abrir app, buscar info)  
✅ Aprendizado incremental com base em feedback  
✅ Interface interativa via terminal ou web

**EN:**  
This project aims to build an intelligent virtual assistant system using Natural Language Processing (NLP) techniques. The assistant can understand natural language commands, answer questions, perform basic actions, and interact contextually with the user.

The system was built from scratch using libraries covered in the course, and meets the following requirements:

✅ Natural language understanding  
✅ Automatic response generation  
✅ Intent and entity recognition  
✅ Execution of basic commands (e.g., open app, search info)  
✅ Incremental learning from feedback  
✅ Interactive interface via terminal or web

---

## ⚙️ Funcionalidades / Features

| 🧩 Funcionalidade (PT)                     | 💡 Description (EN)                          |
|-------------------------------------------|----------------------------------------------|
| 🗣️ Compreensão de linguagem natural        | 🗣️ Natural language understanding             |
| 💬 Geração de respostas automáticas        | 💬 Automatic response generation              |
| 🎯 Reconhecimento de intenções e entidades | 🎯 Intent and entity recognition              |
| 🧾 Execução de comandos simples            | 🧾 Execution of basic commands                |
| 📚 Aprendizado incremental por feedback    | 📚 Incremental learning from feedback         |
| 🖥️ Interface via terminal ou web           | 🖥️ Terminal or web-based interface            |

---

## 🚀 Execução / Execution

**PT:**  
1. Instale as dependências com `npm install` e `pip install -r requirements.txt`  
2. Configure o banco PostgreSQL e variáveis no `.env`  
3. Execute o backend com `python app.py` ou via Docker  
4. Execute o frontend com `npm start`  
5. Interaja com o assistente digitando comandos em linguagem natural  
6. Envie feedback para melhorar o desempenho do sistema  
7. Rode testes automatizados com Cypress

**EN:**  
1. Install dependencies with `npm install` and `pip install -r requirements.txt`  
2. Configure PostgreSQL and environment variables in `.env`  
3. Run backend using `python app.py` or via Docker  
4. Run frontend using `npm start`  
5. Interact with the assistant by typing natural language commands  
6. Submit feedback to improve system performance  
7. Run automated tests with Cypress

---

## 🌐 Acesso / Access

- [🔗 Repositório GitHub / GitHub Repository](https://github.com/Rogerio5/Virtual-Assistant-PLN-Project)

---

## 🧰 Tecnologias / Technologies

<p>
  <img align="left" alt="React" title="React" width="30px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/react/react-original.svg"/>
  <img align="left" alt="Node.js" title="Node.js" width="30px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/nodejs/nodejs-original.svg"/>
  <img align="left" alt="Python" title="Python" width="30px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original.svg"/>
  <img align="left" alt="Tailwind CSS" title="Tailwind CSS" width="30px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/tailwindcss/tailwindcss-original.svg"/>
  <img align="left" alt="PostgreSQL" title="PostgreSQL" width="30px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/postgresql/postgresql-original.svg"/>
  <img align="left" alt="Docker" title="Docker" width="30px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/docker/docker-original.svg"/>
  <img align="left" alt="spaCy" title="spaCy" width="30px" src="https://raw.githubusercontent.com/explosion/spaCy/master/website/src/images/logo.svg"/>
  <img align="left" alt="Cypress" title="Cypress" width="30px" src="https://raw.githubusercontent.com/Krishnanand2517/Krishnanand2517/main/Cypress_Logomark_White-Color.svg"/>
  
</p>

<br clear="all"/>

---

## 📊 Diagrama ASCII da Arquitetura
```
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
```
Fluxo:
1. Usuário interage via Frontend (texto ou áudio).
2. Backend processa entrada (NLP, Whisper, TTS, comandos).
3. Feedbacks e dados são persistidos no Banco de Dados.
4. Dashboard consome dados do Banco e gera relatórios interativos.

---

## 🔄 Fluxo de Requisição
```
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
```
Feedbacks → Banco de Dados (PostgreSQL) → Dashboard (Streamlit)

---

## 📝 Fluxo de Feedbacks
```
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
```

---

## ⚙️ Configuração do backend/config.py

Este projeto usa **FastAPI + Pydantic v2 + pydantic-settings** para carregar variáveis de ambiente do arquivo `.env`.  
Existem duas formas de configurar o `config.py`:

### 🔹 Opção 1 – Declarar todos os campos explicitamente (mais segura)

Nesta abordagem, todas as variáveis esperadas no `.env` são declaradas na classe `Settings`.  
O Pydantic valida cada campo, garantindo consistência e segurança.

```python
from functools import lru_cache
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = Field(default="Virtual Assistant PLN")
    VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=True)

    # Banco de dados
    DATABASE_URL: str | None = None
    DB_NAME: str | None = None
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_HOST: str | None = None
    DB_PORT: str | None = None

    # SMTP
    SMTP_EMAIL: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_SERVER: str | None = None
    SMTP_PORT: str | None = None

    # JWT
    JWT_ALGORITHM: str | None = None

    # SendGrid
    SENDGRID_API_KEY: str | None = None

    # AWS
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```
✅ Vantagem: validação forte, segurança.
❌ Desvantagem: precisa declarar todas as variáveis.

---

### 🔹 Opção 2 – Permitir variáveis extras automaticamente (mais rápida)

Nesta abordagem, você declara apenas o essencial e permite que variáveis extras sejam aceitas sem erro.
É útil para desenvolvimento ou prototipagem rápida.
```
from functools import lru_cache
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = Field(default="Virtual Assistant PLN")
    VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=True)

    DB_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/assistant_db",
        description="URL de conexão com banco de dados PostgreSQL"
    )

    SECRET_KEY: str = Field(default="supersecret")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"   # <-- aceita variáveis extras sem erro

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```
✅ Vantagem: rápido, não quebra se tiver variáveis extras.
❌ Desvantagem: menos validação, pode passar despercebido se faltar algo.

Opção 1 → ideal para produção, garante consistência e validação.
Opção 2 → ideal para desenvolvimento/testes, sobe rápido sem precisar declarar tudo.

---

### 🔒 Futuro (produção) – validação completa

Na versão de produção, recomendamos declarar explicitamente todas as variáveis esperadas no .env, como:

Banco de dados: DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

SMTP: SMTP_EMAIL, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT

Segurança: JWT_ALGORITHM, SECRET_KEY, SENDGRID_API_KEY, AWS_SECRET_ACCESS_KEY

Isso garante validação automática e evita erros silenciosos.

---

### 👨‍💻 Desenvolvedor / Developer

- [Rogerio](https://github.com/Rogerio5)
- [Ronaldo](https://github.com/Ronaldo94-GITHUB)

---

### 📜 Licença / License

Este projeto está sob licença MIT. Para mais detalhes, veja o arquivo LICENSE.
This project is under the MIT license. For more details, see the LICENSE file.

---

### 🏁 Conclusão / Conclusion

PT:  
Este sistema de assistência virtual representa uma aplicação prática e escalável de PLN, com potencial para evoluir em interfaces conversacionais mais complexas, como chatbots, agentes de suporte ou assistentes pessoais. A arquitetura moderna com React, Node.js, IA e PostgreSQL garante flexibilidade e performance.

EN:  
This virtual assistant system represents a practical and scalable application of NLP, with potential to evolve into more complex conversational interfaces such as chatbots, support agents, or personal assistants. The modern architecture using React, Node.js, AI, and PostgreSQL ensures flexibility and performance.
