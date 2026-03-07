"""
telegram_report.py — Yelden Protocol
======================================
Posta o score diário do agente no canal @yeldenfund.
"""
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
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

def score_bar(score: int, width: int = 10) -> str:
    filled = round(score / 1000 * width)
    return "█" * filled + "░" * (width - filled)

def pct_of_max(score: int) -> float:
    return round(score / 1000 * 100, 1)

def format_message(perf, receipt, state) -> str:
    score_acc   = state.get("accumulated_score",
                  perf.get("accumulated_score",
                  perf.get("consistency_score", 0)))
    score_batch = perf.get("consistency_score", 0)

    trades_batch    = perf.get("total_trades", 0)
    trades_lifetime = state.get("total_trades_lifetime", trades_batch)

    win_rate_acc = state.get("win_rate_lifetime",  perf.get("win_rate", 0)) * 100
    sharpe_acc   = state.get("sharpe_lifetime",    perf.get("sharpe_ratio", 0))
    profit_acc   = state.get("total_profit_lifetime", perf.get("total_profit", 0))
    max_dd_acc   = state.get("max_drawdown_lifetime",  perf.get("max_drawdown", 0))

    win_rate_b = perf.get("win_rate", 0) * 100
    sharpe_b   = perf.get("sharpe_ratio", 0)
    profit_b   = perf.get("total_profit", 0)
    avg_r_b    = perf.get("avg_r_multiple", 0)

    date    = perf.get("window_end", perf.get("window_start", ""))[:10]
    tx_hash = receipt.get("tx", receipt.get("tx_hash", "")) if receipt else ""

    acc_pct      = pct_of_max(score_acc)
    profit_b_str = f"+${profit_b:.2f}" if profit_b >= 0 else f"-${abs(profit_b):.2f}"
    profit_a_str = f"+${profit_acc:.2f}" if profit_acc >= 0 else f"-${abs(profit_acc):.2f}"

    lines = [
        f"📊 Markowitz Bot  |  {date}",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"",
        f"⚡ PERFORMANCE ACUMULADA",
        f"Score     {score_acc}/1000  ({acc_pct}% do máx.)",
        f"{score_bar(score_acc)}",
        f"",
        f"Trades    {trades_lifetime} total",
        f"Win rate  {win_rate_acc:.1f}%",
        f"Sharpe    {sharpe_acc:.2f}",
        f"Lucro     {profit_a_str}",
        f"Max DD    ${max_dd_acc:.2f}",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"",
        f"🔄 Última janela ({trades_batch} trades)",
        f"Score     {score_batch}/1000",
        f"Win rate  {win_rate_b:.1f}%  |  Sharpe {sharpe_b:.2f}",
        f"Avg R     {avg_r_b:.3f}  |  P&L {profit_b_str}",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]

    if tx_hash:
        short = tx_hash[:10] + "..." + tx_hash[-6:]
        lines.append(f"🔗 On-chain: {short}")
        lines.append(f"polygonscan.com/tx/{tx_hash}")
        lines.append(f"")

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
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if data.get("ok"):
            print("Telegram: mensagem enviada ao canal")
            return True
        payload["parse_mode"] = ""
        resp2 = requests.post(url, json=payload, timeout=10)
        data2 = resp2.json()
        if data2.get("ok"):
            print("Telegram: mensagem enviada (plain text)")
            return True
        print(f"Telegram erro: {data2.get('description')}")
        return False
    except Exception as e:
        print(f"Telegram exception: {e}")
        return False

def main():
    perf    = load_json("agent_performance.json")
    receipt = load_json("submission_receipt.json")
    state   = load_json("mt5_monitor_state.json") or {}

    if not perf:
        print("agent_performance.json nao encontrado")
        return

    msg = format_message(perf, receipt, state)
    print("── Preview ──────────────────────────────────")
    print(msg)
    print("─────────────────────────────────────────────")
    send_message(msg)

if __name__ == "__main__":
    main()
