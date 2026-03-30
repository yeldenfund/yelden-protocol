"""
generate_agent_data.py — Envia dados do agente para yelden.fund via REST API
Corre após cada run do bridge (adicionar ao run_bridge.bat)
"""
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

REGISTRY_ADDRESS = "0x32F534265090d8645652b76754B07E6648b51571"
AGENT_ADDRESS    = os.getenv("AGENT_ADDRESS", "0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc")
WP_ENDPOINT      = "https://yelden.fund/wp-json/yelden/v1/agent"
WP_TOKEN         = "yelden-2026-markowitz"

def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}

def main():
    perf    = load_json("agent_performance.json")
    state   = load_json("mt5_monitor_state.json")
    receipt = load_json("submission_receipt.json")

    acc_score   = state.get("accumulated_score",
                  perf.get("accumulated_score",
                  perf.get("consistency_score", 0)))
    batch_score = perf.get("consistency_score", 0)

    total_trades = state.get("total_trades_lifetime", perf.get("total_trades", 0))
    win_rate     = state.get("win_rate_lifetime",     perf.get("win_rate", 0))
    sharpe       = state.get("sharpe_lifetime",       perf.get("sharpe_ratio", 0))
    profit       = state.get("total_profit_lifetime", perf.get("total_profit", 0))
    max_dd       = state.get("max_drawdown_lifetime", perf.get("max_drawdown", 0))
    avg_r        = state.get("avg_r_lifetime",        perf.get("avg_r_multiple", 0))

    last_tx     = receipt.get("tx", receipt.get("tx_hash", ""))
    last_date   = perf.get("window_end", perf.get("window_start", ""))[:10]
    last_trades = perf.get("total_trades", 0)

    raw_history   = state.get("score_history", [])
    score_history = []
    running_acc   = 0
    running_total = 0

    for entry in raw_history:
        batch  = entry.get("score", entry.get("batch", 0))
        trades = entry.get("trades", 1)
        ts     = entry.get("timestamp", "")
        date   = ts[:10] if ts else ""
        tx     = entry.get("tx", "")
        if running_total == 0:
            running_acc = batch
        else:
            w = trades / (running_total + trades)
            running_acc = round(running_acc * (1 - w) + batch * w)
        running_total += trades
        score_history.append({"date": date, "trades": trades, "batch": batch, "accumulated": running_acc, "tx": tx})

    if not score_history and batch_score:
        score_history = [{"date": last_date, "trades": last_trades, "batch": batch_score, "accumulated": acc_score, "tx": last_tx}]

    data = {
        "network":               "polygon",
        "registry_address":      REGISTRY_ADDRESS,
        "agent_address":         AGENT_ADDRESS,
        "agent_name":            "Markowitz Trading Bot",
        "agent_type":            "TRADING",
        "erc_id":                "27703",
        "stake_yld":             50,
        "accumulated_score":     int(acc_score),
        "last_batch_score":      int(batch_score),
        "total_trades_lifetime": int(total_trades),
        "win_rate_lifetime":     round(float(win_rate), 4),
        "sharpe_lifetime":       round(float(sharpe), 4),
        "total_profit_lifetime": round(float(profit), 2),
        "max_drawdown_lifetime": round(float(max_dd), 2),
        "avg_r_lifetime":        round(float(avg_r), 4),
        "score_history":         score_history,
        "last_updated":          datetime.now(timezone.utc).isoformat(),
        "last_tx":               last_tx,
    }

    # Guarda cópia local
    with open("agent_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Envia para o WordPress
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        WP_ENDPOINT,
        data=payload,
        headers={
            "Content-Type":   "application/json",
            "X-Yelden-Token": WP_TOKEN,
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            print(f"✓ Dashboard actualizado: score={data['accumulated_score']}, trades={data['total_trades_lifetime']}")
            print(f"  Resposta WP: {result}")
    except urllib.error.HTTPError as e:
        print(f"✗ Erro HTTP {e.code}: {e.read().decode()}")
    except Exception as e:
        print(f"✗ Erro ao enviar para WordPress: {e}")
        print("  (dados guardados em agent_data.json localmente)")

if __name__ == "__main__":
    main()
