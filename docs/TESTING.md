
---

## 📄 `TESTING.md`

```markdown
# 🧪 Guia de Testes

## Backend
- Testes escritos com **pytest**.
- Rodar todos os testes:
  ```bash
  pytest -v

Cobertura de código:
```
pytest --cov=backend --cov-report=term-missing


## Frontend
Testes de interface com Cypress.

Rodar:
```
npx cypress open
```

## Estrutura de testes
tests/test_api.py: endpoints principais.

tests/test_assistant.py: fluxo de comandos.

tests/test_entities.py: extração de entidades.

tests/test_intents.py: classificação de intenções.

## Boas práticas
Sempre criar testes para novas features.

Usar mocks para evitar dependências externas pesadas (ex.: Whisper, OpenAI).