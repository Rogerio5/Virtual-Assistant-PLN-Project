
---

## 📄 `DEPLOYMENT.md`

```markdown
# 🚀 Guia de Deploy

Este documento descreve como colocar o projeto em produção.

## 🔧 Pré-requisitos
- Docker e Docker Compose instalados.
- Variáveis de ambiente configuradas em `.env`:
  - `JWT_SECRET` forte.
  - `COOKIE_SECURE=true` (para HTTPS).
  - Credenciais do banco PostgreSQL.

## 📦 Deploy com Docker Compose
```bash
docker-compose -f docker/docker-compose.yml up --build -d
```

## 🌐 Configuração de CORS
No backend (app.py), ajuste:
```
allow_origins=["https://seu-dominio.com"]
```

## 🔒 Segurança
Use HTTPS (TLS).

Configure firewall para expor apenas portas necessárias.

Gere logs e monitore erros.

## 📊 Monitoramento
Use ferramentas como Prometheus + Grafana ou ELK Stack.

Configure alertas para falhas no backend ou dashboard.

