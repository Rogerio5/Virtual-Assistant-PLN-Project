# 🤖 Virtual Assistant PLN Project

Assistente virtual com **processamento de linguagem natural (PLN)**, **reconhecimento de voz** e **dashboard de feedbacks**.

---

## ✨ Funcionalidades
- Processamento de texto e voz
- Classificação de intenções e extração de entidades
- Execução de comandos (YouTube, Wikipedia)
- Feedback dos usuários
- Dashboard interativo e relatórios em PDF/Excel

---

## ⚙️ Instalação

```bash
git clone https://github.com/seu-repo.git
cd VIRTUAL-ASSISTANT-PLN-PROJECT
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt


🚀 Como Rodar
Backend (FastAPI)

uvicorn backend.app:app --reload

---

Frontend (React)

cd frontend
npm install
npm start

---

Dashboard (Streamlit)

streamlit run dash/dashboard_streamlit.py

---

Docker Compose 

docker-compose -f docker/docker-compose.yml up --build

---

🧪 Testes
Backend: pytest

Frontend: npx cypress open

---

🤝 Contribuição
Faça um fork do projeto.

Crie uma branch (git checkout -b feature/nova-feature).

Commit suas alterações (git commit -m 'Adiciona nova feature').

Push para a branch (git push origin feature/nova-feature).

Abra um Pull Request.

---

📜 Licença
Este projeto está sob a licença MIT.
🎯 Agora você tem os três arquivos (`API.md`, `ARCHITECTURE.md`, `README.md`) completos em Markdown, prontos para copiar e colar na pasta **docs**.  