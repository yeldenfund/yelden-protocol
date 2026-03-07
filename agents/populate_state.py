"""
populate_state.py — Popula mt5_monitor_state.json com histórico completo do MT5
Corre em: pasta agents no VPS
Executa UMA VEZ para inicializar o state acumulado.
"""
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    import MetaTrader5 as mt5
except ImportError:
    print("❌ MetaTrader5 não instalado")
    exit(1)

STATE_PATH = "mt5_monitor_state.json"
MAGIC      = 975311  # magic number do Markowitz bot

print("=" * 60)
print("POPULATE STATE — Histórico completo do MT5")
print("=" * 60)

# ── Conectar MT5 ──────────────────────────────────────────────
if not mt5.initialize():
    print(f"❌ MT5 não iniciou: {mt5.last_error()}")
    exit(1)

info = mt5.account_info()
print(f"✅ Conectado: {info.login} | {info.server} | Balance: ${info.balance:.2f}")

# ── Buscar TODO o histórico com magic=975311 ──────────────────
from datetime import timezone
date_from = datetime(2020, 1, 1, tzinfo=timezone.utc)
date_to   = datetime.now(timezone.utc)

deals = mt5.history_deals_get(date_from, date_to)
mt5.shutdown()

if deals is None or len(deals) == 0:
    print("❌ Nenhum deal encontrado")
    exit(1)

print(f"✅ {len(deals)} deals encontrados no histórico total")

# ── Filtrar por magic e tipo DEAL_TYPE_BUY/SELL (saídas) ──────
import MetaTrader5 as mt5_const

DEAL_ENTRY_OUT = 1  # saída de posição

trades = []
for d in deals:
    if d.magic != MAGIC:
        continue
    if d.entry != DEAL_ENTRY_OUT:
        continue
    if d.profit == 0:
        continue
    trades.append(d)

print(f"✅ {len(trades)} trades fechados pelo Markowitz bot")

if len(trades) == 0:
    print("⚠️  Nenhum trade com magic={MAGIC} encontrado")
    exit(1)

# ── Calcular métricas acumuladas ──────────────────────────────
profits     = [t.profit for t in trades]
winning     = [p for p in profits if p > 0]
total_profit = sum(profits)
win_rate     = len(winning) / len(profits)
avg_profit   = total_profit / len(profits)

# Sharpe simplificado
import statistics
if len(profits) > 1:
    std = statistics.stdev(profits)
    sharpe = (avg_profit / std) * (252 ** 0.5) if std > 0 else 0
else:
    sharpe = 0

# Max drawdown
peak = 0
equity = 0
max_dd = 0
for p in profits:
    equity += p
    if equity > peak:
        peak = equity
    dd = peak - equity
    if dd > max_dd:
        max_dd = dd

# Avg R (usar profit normalizado — aproximação)
avg_r = sum(abs(p) / max(abs(p), 1) * (1 if p > 0 else -1) for p in profits) / len(profits)

last_ticket = max(t.ticket for t in trades)
last_trade_time = datetime.fromtimestamp(
    max(t.time for t in trades)).isoformat()

print()
print("── Métricas acumuladas ────────────────────────────────────")
print(f"   Total trades  : {len(trades)}")
print(f"   Win rate      : {win_rate*100:.1f}%")
print(f"   Total profit  : ${total_profit:.2f}")
print(f"   Sharpe        : {sharpe:.2f}")
print(f"   Max DD        : ${max_dd:.2f}")
print(f"   Last ticket   : {last_ticket}")

# ── Ler state actual para preservar last_score ────────────────
current_state = {}
if os.path.exists(STATE_PATH):
    with open(STATE_PATH) as f:
        current_state = json.load(f)

last_score = current_state.get("last_score", 989)

# ── Escrever state completo ───────────────────────────────────
new_state = {
    # campos originais — não quebrar compatibilidade
    "last_ticket":  last_ticket,
    "last_check":   datetime.now().isoformat(),
    "last_score":   last_score,

    # campos acumulados — novos
    "accumulated_score":       last_score,
    "total_trades_lifetime":   len(trades),
    "win_rate_lifetime":       win_rate,
    "sharpe_lifetime":         round(sharpe, 4),
    "total_profit_lifetime":   round(total_profit, 2),
    "max_drawdown_lifetime":   round(max_dd, 2),
    "avg_r_lifetime":          round(avg_r, 4),
    "first_trade_time":        datetime.fromtimestamp(
                                   min(t.time for t in trades)).isoformat(),
    "last_trade_time":         last_trade_time,
}

with open(STATE_PATH, "w") as f:
    json.dump(new_state, f, indent=2)

print()
print(f"✅ State guardado em {STATE_PATH}")
print()
print("── Preview do próximo post Telegram ───────────────────────")
print(f"   Score     {last_score}/1000  ({last_score/10:.1f}% do máx.)")
print(f"   Trades    {len(trades)} total")
print(f"   Win rate  {win_rate*100:.1f}%")
print(f"   Sharpe    {sharpe:.2f}")
print(f"   Lucro     +${total_profit:.2f}")
print(f"   Max DD    ${max_dd:.2f}")
print()
print("Próxima run do bridge vai usar estes valores no acumulado.")
print()
input("Prima ENTER para sair...")
