@echo off
echo ============================================
echo  Yelden Protocol - Agent Bridge
echo ============================================
echo.

cd /d C:\Users\Administrator\yelden-protocol\agents

echo [1/2] Buscando trades fechados no MT5...
python mt5_monitor.py
if errorlevel 1 (
    echo ERRO no monitor - abortando
    pause
    exit /b 1
)

echo.
echo [2/2] Enviando score para Sepolia...
echo s | python yelden_reporter.py

echo [3/3] Postando no Telegram...
python telegram_report.py

echo.
echo ============================================
echo  Concluido! Verifique submission_receipt.json
echo ============================================
pause