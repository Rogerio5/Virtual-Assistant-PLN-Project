Write-Host "🧪 Rodando testes automatizados..."

# Ativar ambiente virtual (ajuste para venv ou venv312)
.\venv312\Scripts\activate

# Rodar pytest com relatório de cobertura
pytest --asyncio-mode=auto --cov=backend --cov-report=term-missing
