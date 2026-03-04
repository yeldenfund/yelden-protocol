@echo off
echo ============================================
echo  Yelden Protocol - Agent Bridge
echo ============================================
echo.

cd /d C:\Users\Paulo\yelden-protocol\agents
C:\Python314\python.exe mt5_monitor.py

echo [1/2] Buscando trades fechados no MT5...

if errorlevel 1 (
    echo ERRO no monitor - abortando
    pause
    exit /b 1
)

echo.
echo [2/2] Enviando score para Sepolia...
echo s | C:\Python314\python.exe yelden_reporter.py

echo.
echo ============================================
echo  Concluido! Verifique submission_receipt.json
echo ============================================
pause