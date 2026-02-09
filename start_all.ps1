# Ativar ambiente virtual
Write-Host "🔧 Ativando ambiente virtual..."
& "$PSScriptRoot\venv312\Scripts\Activate.ps1"

# Abrir Backend (FastAPI)
Write-Host "🚀 Iniciando Backend (FastAPI)..."
Start-Process powershell -ArgumentList "uvicorn backend.app:app --reload --port 8000"

# Abrir Frontend (React)
Write-Host "🎨 Iniciando Frontend (React)..."
Start-Process powershell -ArgumentList "cd $PSScriptRoot\frontend; npm run dev"

# Abrir Dashboard (Streamlit)
Write-Host "📊 Iniciando Dashboard (Streamlit)..."
Start-Process powershell -ArgumentList "streamlit run dashboard.py"

Write-Host "✅ Todos os serviços foram iniciados!"
