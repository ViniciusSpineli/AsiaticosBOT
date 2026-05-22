@echo off
chcp 65001 >nul
cls
echo.
echo Monitor Ao Vivo - Estrategia do Funil
echo ========================================
echo.

cd /d "C:\Users\vinic\OneDrive\Área de Trabalho\Projetos_Python\BET_365\bet365_funil_strategy"

if not exist "venv\Scripts\python.exe" (
  echo [ERRO] Ambiente virtual nao encontrado em venv\Scripts\python.exe
  echo Rode antes: python -m venv venv
  pause
  exit /b 1
)

echo Verificando dependencias...
venv\Scripts\python.exe -m pip show requests >nul 2>&1
if errorlevel 1 (
  echo Instalando dependencias...
  venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
  )
)

echo Ambiente pronto!
echo.
echo Iniciando monitor continuo (intervalo 30s, feed maximo 120s)...
echo Enviando 1 sinal de vida de jogo ao vivo no Telegram...
echo.

venv\Scripts\python.exe live_monitor.py --file live_matches.json --interval 30 --max-feed-age 120 --send-live-sample

echo.
echo ========================================
echo Monitor encerrado
echo ========================================
pause
