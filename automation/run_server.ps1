Write-Host "🚀 Iniciando servidor FastAPI/Uvicorn..."

# Ativar ambiente virtual (ajuste para venv ou venv312)
.\venv312\Scripts\activate

# Rodar servidor na porta 8000
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
