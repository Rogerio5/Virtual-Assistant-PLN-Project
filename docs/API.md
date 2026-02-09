# 📡 Documentação da API - Assistente Virtual PLN

Esta API fornece endpoints para processamento de linguagem natural (PLN), reconhecimento de voz e coleta de feedbacks dos usuários.

---

## 🔑 Autenticação
Atualmente os endpoints não exigem autenticação. Futuramente será implementado JWT baseado em `SECRET_KEY` e `JWT_ALGORITHM`.

---

## 📍 Endpoints

### Health Check
`GET /`
- **Descrição**: Verifica se a API está rodando.
- **Resposta**:
```json
{
  "message": "Assistente Virtual PLN rodando com sucesso 🚀",
  "debug": true
}

---

Informações do Projeto

GET /info

Descrição: Retorna informações sobre o projeto.

Resposta:
{
  "project": "Virtual Assistant PLN",
  "version": "1.0.0",
  "author": "Rogerio",
  "features": [
    "Processamento de linguagem natural",
    "Reconhecimento de voz",
    "Síntese de voz",
    "Banco de dados com SQLAlchemy",
    "Autenticação JWT"
  ]
}

---

Processar Comando
POST /assistant/process

Descrição: Processa áudio ou texto e retorna resposta.

Request Body:
{
  "audio_file": "saida.wav",
  "text_input": "Quero ouvir Djavan"
}

Resposta:
{
  "input": "Quero ouvir Djavan",
  "response": "Tocando sua música favorita!",
  "audio": "response_abcd1234.mp3"
}

---

Enviar Feedback
POST /feedback

Descrição: Salva feedback do usuário.

Request Body:
{
  "user_id": "rogerio",
  "message": "Gostei do assistente",
  "rating": 5
}

Resposta:
{
  "status": "Feedback recebido com sucesso!",
  "saved": true
}

---

⚠️ Códigos de Erro
400 → Entrada inválida

404 → Rota não encontrada

500 → Erro interno do servidor
