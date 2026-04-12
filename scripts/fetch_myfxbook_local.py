"""
fetch_myfxbook_local.py — Corre no teu PC LOCAL (nao no VPS)
Faz login no Myfxbook, busca os dados, e envia directamente para o WordPress.

Uso:
    python fetch_myfxbook_local.py

Podes agendar no Windows Task Scheduler para correr diariamente.
Nao precisa de estar no VPS.
"""
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import requests
import json
import os
from datetime import datetime, timedelta, timezone

# ── Config ────────────────────────────────────────────────────
EMAIL       = "plongen@gmail.com"
PASSWORD    = "qA_XYf!:Ki43Jzw"          # preenche aqui ou usa .env
WP_ENDPOINT = "https://yelden.fund/wp-json/yelden/v1/myfxbook"
WP_TOKEN    = "yelden-2026-markowitz"
BASE        = "https://www.myfxbook.com/api"

# Tenta ler do .env se existir
try:
    from dotenv import load_dotenv
    load_dotenv()
    EMAIL    = os.getenv("MYFXBOOK_EMAIL",    EMAIL)
    PASSWORD = os.getenv("MYFXBOOK_PASSWORD", PASSWORD)
except ImportError:
    pass

def api(endpoint, params):
    r = requests.get(f"{BASE}/{endpoint}.json", params=params, timeout=15)
    return r.json()

def main():
    # 1. Login
    print("Myfxbook: a fazer login...")
    login = api("login", {"email": EMAIL, "password": PASSWORD})
    if login.get("error"):
        print(f"✗ Login falhou: {login.get('message')}")
        return
    session = login["session"]
    print(f"  ✓ Sessão: {session[:8]}...")

    # 2. Contas
    accounts_data = api("get-my-accounts", {"session": session})
    if accounts_data.get("error"):
        print(f"✗ get-my-accounts: {accounts_data.get('message')}")
        api("logout", {"session": session})
        return

    accounts = accounts_data.get("accounts", [])
    if not accounts:
        print("✗ Nenhuma conta encontrada")
        api("logout", {"session": session})
        return

    # Lista todas as contas
    print(f"  Contas encontradas: {len(accounts)}")
    for a in accounts:
        print(f"    [{a.get('id')}] {a.get('name')} | gain={a.get('gain')}% | trades={a.get('trades')} | demo={a.get('demo')}")

    acc        = accounts[0]
    account_id = acc["id"]
    print(f"\n  A usar: {acc.get('name')} (id={account_id})")

    # 3. Histórico de trades
    date_from   = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    date_to     = datetime.now().strftime("%Y-%m-%d")
    history     = api("get-history",    {"session": session, "id": account_id, "start": date_from, "end": date_to})
    daily       = api("get-data-daily", {"session": session, "id": account_id, "start": date_from, "end": date_to})

    trades_list = [] if history.get("error") else history.get("history",   [])
    daily_list  = [] if daily.get("error")   else daily.get("dataDaily",   [])
    print(f"  Trades ({date_from} → {date_to}): {len(trades_list)}")
    print(f"  Dias com dados: {len(daily_list)}")

    # 4. Logout
    api("logout", {"session": session})

    # 5. Monta payload
    trades_total = int(acc.get("trades", 0))
    won          = int(acc.get("wonTrades", 0))
    win_rate     = round(won / trades_total * 100, 2) if trades_total > 0 else 0.0

    data = {
        "account_id":    str(account_id),
        "url":           f"https://www.myfxbook.com/portfolio/markowitz-bot/{account_id}",
        "name":          acc.get("name",          f"Conta #{account_id}"),
        "gain":          float(acc.get("gain",          0)),
        "abs_gain":      float(acc.get("absGain",       0)),
        "daily":         float(acc.get("daily",         0)),
        "monthly":       float(acc.get("monthly",       0)),
        "drawdown":      float(acc.get("drawdown",      0)),
        "balance":       float(acc.get("balance",       0)),
        "profit":        float(acc.get("profit",        0)),
        "trades":        trades_total,
        "win_rate":      win_rate,
        "profit_factor": float(acc.get("profitFactor",  1.0)),
        "pips":          float(acc.get("pips",          0)),
        "currency":      acc.get("currency",            "USD"),
        "demo":          acc.get("demo",                False),
        "last_update":   acc.get("lastUpdateDate",      ""),
        "source":        "api_auth",
        "fetched_at":    datetime.now(timezone.utc).isoformat(),
        "trades_detail": trades_list[:200],
        "daily_detail":  daily_list[-90:],
    }

    # Guarda localmente
    with open("myfxbook_raw.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"  myfxbook_raw.json guardado")

    # 6. Envia para WordPress
    print("\nA enviar para yelden.fund...")
    try:
        resp = requests.post(
            WP_ENDPOINT,
            json=data,
            headers={"X-Yelden-Token": WP_TOKEN},
            timeout=15,
        )
        result = resp.json()
        if resp.status_code == 200 and result.get("ok"):
            print(f"  ✓ Dashboard /join actualizado!")
        else:
            print(f"  ✗ WP error {resp.status_code}: {result}")
    except Exception as e:
        print(f"  ✗ WP error: {e}")

if __name__ == "__main__":
    main()
