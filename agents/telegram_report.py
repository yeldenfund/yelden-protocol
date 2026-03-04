"""
telegram_report.py — Yelden Protocol
======================================
Posta o score diário do agente no canal @yeldenfund.
"""

import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1003567429786")

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

def score_bar(score: int) -> str:
    filled = int(score / 100)
    return "█" * filled + "░" * (10 - filled)

def format_message(perf, receipt, state) -> str:
    score_acc   = state.get("accumulated_score", perf.get("accumulated_score", perf.get("consistency_score", 0)))
    score_batch = perf.get("consistency_score", 0)
    win_rate    = perf.get("win_rate", 0) * 100
    trades      = perf.get("total_trades", 0)
    lifetime    = state.get("total_trades_lifetime", trades)
    profit      = perf.get("total_profit", 0)
    sharpe      = perf.get("sharpe_ratio", 0)
    max_dd      = perf.get("max_drawdown", 0)
    avg_r       = perf.get("avg_r_multiple", 0)
    date        = perf.get("window_end", "")[:10]
    tx_hash     = receipt.get("tx_hash", "") if receipt else ""

    profit_str = f"+${profit:.2f}" if profit >= 0 else f"-${abs(profit):.2f}"
    dd_str     = f"${max_dd:.2f}"

    lines = [
        f"📊 Markowitz Trading Bot — Daily Report",
        f"📅 {date}",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"Score acumulado:  {score_acc}/1000",
        f"{score_bar(score_acc)}",
        f"",
        f"Score batch:   {score_batch}/1000",
        f"Trades batch:  {trades}",
        f"Trades total:  {lifetime}",
        f"Win rate:      {win_rate:.1f}%",
        f"Sharpe:        {sharpe:.2f}",
        f"Avg R:         {avg_r:.3f}",
        f"Max DD:        {dd_str}",
        f"Lucro batch:   {profit_str}",
        f"━━━━━━━━━━━━━━━━━━━━━━",
    ]

    if tx_hash:
        short = tx_hash[:10] + "..." + tx_hash[-6:]
        lines.append(f"🔗 On-chain: {short}")
        lines.append(f"sepolia.etherscan.io/tx/{tx_hash}")

    lines.append("")
    lines.append("github.com/yeldenfund/yelden-protocol")

    return "\n".join(lines)

def send_message(text: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    # Try HTML first, fallback to plain
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if data.get("ok"):
            print("✅ Telegram: mensagem enviada ao canal")
            return True
        # Fallback: plain text
        payload["parse_mode"] = ""
        resp2 = requests.post(url, json=payload, timeout=10)
        data2 = resp2.json()
        if data2.get("ok"):
            print("✅ Telegram: mensagem enviada (plain text)")
            return True
        print(f"❌ Telegram erro: {data2.get('description')}")
        return False
    except Exception as e:
        print(f"❌ Telegram exception: {e}")
        return False

def main():
    perf    = load_json("agent_performance.json")
    receipt = load_json("submission_receipt.json")
    state   = load_json("mt5_monitor_state.json") or {}

    if not perf:
        print("⚠️ agent_performance.json não encontrado")
        return

    msg = format_message(perf, receipt, state)
    send_message(msg)

if __name__ == "__main__":
    main()
