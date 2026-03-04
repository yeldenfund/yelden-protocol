"""
agent_bridge.py — Yelden Protocol Agent Bridge Coordinator
===========================================================
Orchestrates the complete flow with .env configuration.
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from dotenv import load_dotenv

# Carrega configurações
load_dotenv()

AGENT_ADDRESS = os.getenv("AGENT_ADDRESS")
MT5_PATH = os.getenv("MT5_PATH", r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe")

def run_monitor() -> bool:
    """Execute mt5_monitor.py"""
    print("\n🔍 Passo 1: Verificando novos trades...")
    
    cmd = [sys.executable, "mt5_monitor.py"]
    if MT5_PATH:
        cmd.extend(["--mt5-path", MT5_PATH])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Erros:", result.stderr)
    
    return os.path.exists("agent_performance.json")

def run_reporter() -> bool:
    """Execute yelden_reporter.py"""
    print("\n📤 Passo 2: Submetendo ao Registry...")
    
    result = subprocess.run(
        [sys.executable, "yelden_reporter.py"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Erros:", result.stderr)
    
    return "✅ Sucesso" in result.stdout or "✅ Transação enviada" in result.stdout

def main():
    print("=" * 60)
    print("Yelden Protocol - Agent Bridge")
    print("=" * 60)
    print(f"Ambiente: {os.getenv('ETH_RPC_URL', 'não configurado')[:30]}...")
    print(f"Agente:   {AGENT_ADDRESS[:10]}...")
    
    # Verifica se .env está configurado
    if not AGENT_ADDRESS or AGENT_ADDRESS == "0xSeuEnderecoEthereumAqui":
        print("\n❌ Configure o arquivo .env primeiro!")
        print("   Copie .env.example para .env e edite com seus dados")
        return
    
    # Passo 1: Monitor
    if not run_monitor():
        print("\n❌ Nenhum trade novo encontrado")
        return
    
    time.sleep(1)
    
    # Passo 2: Report
    if run_reporter():
        print("\n🎉 Bridge executado com sucesso!")
    else:
        print("\n❌ Falha na execução")

if __name__ == "__main__":
    main()
