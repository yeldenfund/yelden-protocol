@echo off
echo ============================================
echo  Yelden Protocol - Agent Bridge
echo ============================================
echo.

cd /d C:\Users\Paulo\yelden-protocol\agents

echo [1/2] Buscando trades fechados no MT5...
C:\Python314\python.exe mt5_monitor.py
if errorlevel 1 (
    echo ERRO no monitor - abortando
    pause
    exit /b 1
)

if not exist agent_performance.json goto :sem_trades

echo.
echo [2/2] Enviando score para Sepolia...
echo s | C:\Python314\python.exe yelden_reporter.py
goto :fim

:sem_trades
echo.
echo Nenhum trade novo - nao enviando para blockchain

:fim
echo.
echo ============================================
echo  Concluido!
echo ============================================
pause
