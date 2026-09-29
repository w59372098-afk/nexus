Set-Location "$PSScriptRoot\backend"
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
