"""
generate_agent_data.py — Envia dados do agente para yelden.fund via REST API
v4.2 — fonte de verdade:
  - histórico/trades/score : mt5_monitor_state.json
  - EMA/CF/SF/stage        : yelden_state.json
  - tx/score on-chain      : submission_receipt.json
  - métricas do batch      : agent_performance.json
"""
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

REGISTRY_ADDRESS = "0xbC102cDec0DD007E7739ac213b62d5B031B22aF1"
AGENT_ADDRESS    = os.getenv("AGENT_ADDRESS", "0x84d00C78866A98CC2c7f985bdbF4871c552fF986")
WP_ENDPOINT      = "https://yelden.fund/wp-json/yelden/v1/agent"
WP_TOKEN         = "yelden-2026-markowitz"

def load_json(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def main():
    perf    = load_json("agent_performance.json")
    state   = load_json("yelden_state.json")
    mt5     = load_json("mt5_monitor_state.json")
    receipt = load_json("submission_receipt.json")

    # ── Score on-chain (fonte: submission_receipt) ────────────
    acc_score   = receipt.get("score", mt5.get("accumulated_score", 0))
    batch_score = perf.get("s_raw", 0)

    # ── Métricas lifetime (fonte: agent_performance) ──────────
    total_trades = mt5.get("total_trades_lifetime",
                   perf.get("total_trades_lifetime",
                   perf.get("total_trades", 0)))
    win_rate     = perf.get("win_rate",      0)
    sharpe       = perf.get("sharpe_ratio",  0)
    profit       = perf.get("total_profit",  0)
    max_dd       = perf.get("max_drawdown",  0)
    avg_r        = perf.get("avg_r_multiple",0)

    last_tx = receipt.get("tx", receipt.get("tx_hash", ""))

    # ── Histórico (fonte: mt5_monitor_state.json) ─────────────
    # Cada entry tem: score, trades, timestamp
    raw_history   = mt5.get("score_history", [])
    score_history = []

    for i, entry in enumerate(raw_history):
        score_val = entry.get("score", 0)
        trades    = entry.get("trades", 0)
        ts        = entry.get("timestamp", "")
        date      = ts[:10] if ts else ""
        # tx só na última entry (a mais recente tem o receipt)
        tx = last_tx if i == len(raw_history) - 1 else entry.get("tx", "")

        score_history.append({
            "date":        date,
            "trades":      int(trades),
            "batch":       int(score_val),
            "accumulated": int(acc_score),   # score acumulado actual
            "tx":          tx,
        })

    # Fallback se mt5 não tiver histórico
    if not score_history:
        score_history = [{
            "date":        receipt.get("date", "")[:10],
            "trades":      int(total_trades),
            "batch":       int(acc_score),
            "accumulated": int(acc_score),
            "tx":          last_tx,
        }]

    data = {
        "network":               "polygon",
        "registry_address":      REGISTRY_ADDRESS,
        "agent_address":         AGENT_ADDRESS,
        "agent_name":            "Markowitz Trading Bot",
        "agent_type":            "TRADING",
        "erc_id":                "27703",
        "stake_yld":             50,

        # Score principal
        "accumulated_score":     int(acc_score),
        "last_batch_score":      int(acc_score),   # score submetido on-chain

        # Campos v4.1
        "s_raw":                 round(float(batch_score), 2),
        "stage":                 state.get("stage_last", perf.get("stage", "EXPERIMENTAL")),
        "ema":                   round(float(state.get("ema",      0)), 2),
        "cf":                    round(float(state.get("cf_last",  0)), 4),
        "sf":                    round(float(state.get("sf_last",  0)), 4),
        "scorer_version":        "v4.1",

        # Métricas lifetime
        "total_trades_lifetime": int(total_trades),
        "win_rate_lifetime":     round(float(win_rate), 4),
        "sharpe_lifetime":       round(float(sharpe),   4),
        "total_profit_lifetime": round(float(profit),   2),
        "max_drawdown_lifetime": round(float(max_dd),   2),
        "avg_r_lifetime":        round(float(avg_r),    4),

        # Histórico
        "score_history":         score_history,

        # Meta
        "last_updated":          datetime.now(timezone.utc).isoformat(),
        "last_tx":               last_tx,
    }

    with open("agent_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"agent_data.json gerado:")
    print(f"  Score acc  : {data['accumulated_score']}")
    print(f"  S_raw      : {data['s_raw']}")
    print(f"  Stage      : {data['stage']}")
    print(f"  Trades     : {data['total_trades_lifetime']}")
    print(f"  Win rate   : {data['win_rate_lifetime']*100:.1f}%")
    print(f"  Historico  : {len(score_history)} entradas")
    for h in score_history:
        print(f"    {h['date']}  trades={h['trades']}  batch={h['batch']}  acc={h['accumulated']}")

    # Envia para WordPress
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        WP_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json", "X-Yelden-Token": WP_TOKEN},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            print(f"✓ Dashboard actualizado")
            print(f"  Resposta WP: {result}")
    except urllib.error.HTTPError as e:
        print(f"✗ Erro HTTP {e.code}: {e.read().decode()}")
    except Exception as e:
        print(f"✗ Erro ao enviar: {e}")
        print("  (dados guardados localmente em agent_data.json)")

if __name__ == "__main__":
    main()
