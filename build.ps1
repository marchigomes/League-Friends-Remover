$ErrorActionPreference = 'Stop'
python -m pip install -r requirements-build.txt
python -m PyInstaller --onefile --name RemoverAmigosLoL remover_amigos_lcu.py
Write-Host "Executável criado em dist\RemoverAmigosLoL.exe"
