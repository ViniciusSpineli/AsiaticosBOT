@echo off
chcp 65001 >nul
cls
echo.
echo Sistema de Alerta - Estrategia do Funil (Escanteios Asiaticos)
echo ================================================================
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
echo Executando validacao da estrategia...
echo.

venv\Scripts\python.exe main.py

echo.
echo ================================================================
echo Execucao concluida!
echo ================================================================
pause
