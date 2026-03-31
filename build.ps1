# Build a portable one-file EXE (Windows)
# Usage:
#   .\.venv\Scripts\Activate.ps1
#   pip install -r requirements.txt
#   .\build.ps1

$ErrorActionPreference = 'Stop'

python -m PyInstaller --noconfirm --clean --onefile --windowed `
  --name EdgeHistoryFinder `
  --paths src `
  src/edge_history_finder/__main__.py

Write-Host "Built: dist/EdgeHistoryFinder.exe"
