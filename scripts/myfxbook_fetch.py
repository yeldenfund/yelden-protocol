import requests
import json
from datetime import datetime, timedelta

# ─── CONFIGURACAO ────────────────────────────────────────────
EMAIL    = "plongen@gmail.com"
PASSWORD = "qA_XYf!:Ki43Jzw"
# ─────────────────────────────────────────────────────────────

BASE = "https://www.myfxbook.com/api"

def api(endpoint, params):
    r = requests.get(f"{BASE}/{endpoint}.json", params=params)
    return r.json()

# ── 1. LOGIN ─────────────────────────────────────────────────
print("A ligar ao Myfxbook...")
login = api("login", {"email": EMAIL, "password": PASSWORD})

if login.get("error"):
    print(f"ERRO no login: {login.get('message')}")
    exit()

session = login["session"]
print(f"Sessao obtida: {session[:8]}...")

# ── 2. CONTAS ────────────────────────────────────────────────
print("\n--- CONTAS ---")
accounts_data = api("get-my-accounts", {"session": session})

if accounts_data.get("error"):
    print(f"Erro: {accounts_data.get('message')}")
    exit()

accounts = accounts_data.get("accounts", [])
print(f"Total de contas encontradas: {len(accounts)}\n")

for acc in accounts:
    print(f"  ID:         {acc.get('id')}")
    print(f"  Nome:       {acc.get('name')}")
    print(f"  Broker:     {acc.get('broker')}")
    print(f"  Gain:       {acc.get('gain')}%")
    print(f"  Drawdown:   {acc.get('drawdown')}%")
    print(f"  Trades:     {acc.get('trades')}")
    print(f"  Win Rate:   {acc.get('wonTrades')} wins / {acc.get('trades')} total")
    print(f"  Profit:     {acc.get('profit')}")
    print(f"  Demo:       {acc.get('demo')}")
    print(f"  Privado:    {acc.get('private')}")
    print()

# ── 3. ESCOLHE CONTA ─────────────────────────────────────────
if len(accounts) == 0:
    print("Nenhuma conta encontrada.")
    exit()

# Usa a primeira conta automaticamente
# Podes mudar para input() se quiseres escolher
account_id = accounts[0]["id"]
print(f"A usar conta: {account_id} ({accounts[0]['name']})")

# ── 4. HISTORICO DE TRADES ───────────────────────────────────
print("\n--- HISTORICO DE TRADES ---")
date_from = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
date_to   = datetime.now().strftime("%Y-%m-%d")

history = api("get-history", {
    "session":   session,
    "id":        account_id,
    "start":     date_from,
    "end":       date_to,
})

if history.get("error"):
    print(f"Erro: {history.get('message')}")
else:
    trades = history.get("history", [])
    print(f"Trades no periodo ({date_from} a {date_to}): {len(trades)}")
    if trades:
        print(f"Primeiro trade: {trades[0]}")
        print(f"Ultimo trade:   {trades[-1]}")

# ── 5. DADOS DIARIOS (para Sharpe) ───────────────────────────
print("\n--- DADOS DIARIOS ---")
daily = api("get-data-daily", {
    "session": session,
    "id":      account_id,
    "start":   date_from,
    "end":     date_to,
})

if daily.get("error"):
    print(f"Erro: {daily.get('message')}")
else:
    data = daily.get("dataDaily", [])
    print(f"Dias com dados: {len(data)}")
    if data:
        print(f"Exemplo (ultimo dia): {data[-1]}")

# ── 6. GUARDA TUDO EM JSON ───────────────────────────────────
output = {
    "timestamp":  datetime.now().isoformat(),
    "account_id": account_id,
    "accounts":   accounts,
    "history":    trades if not history.get("error") else [],
    "daily":      data   if not daily.get("error")   else [],
}

with open("myfxbook_raw.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\nDados guardados em myfxbook_raw.json")
print("Envia esse ficheiro para o scorer calcular o S_raw.")

# ── 7. LOGOUT ────────────────────────────────────────────────
api("logout", {"session": session})
print("Sessao terminada.")
