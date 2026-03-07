"""
trade_history.py — Yelden Protocol
====================================
Lê TODOS os trades fechados do MT5 pelo magic number.
Mostra o histórico completo sem filtro de last_ticket.

Uso: python trade_history.py
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

MAGIC_NUMBER = 975311
MT5_PATH     = os.getenv("MT5_PATH", None)

def connect():
    kwargs = {"path": MT5_PATH} if MT5_PATH else {}
    if not mt5.initialize(**kwargs):
        print(f"❌ MT5 connection failed: {mt5.last_error()}")
        return False
    info = mt5.account_info()
    print(f"✅ Connected: {info.login} | {info.server} | Balance: ${info.balance:,.2f}")
    return True

def get_all_trades(days_back=90):
    date_from = datetime.now() - timedelta(days=days_back)
    date_to   = datetime.now()

    deals = mt5.history_deals_get(date_from, date_to)
    if deals is None:
        print(f"⚠️ No deals: {mt5.last_error()}")
        return []

    closing = [
        d for d in deals
        if d.magic == MAGIC_NUMBER
        and d.entry == mt5.DEAL_ENTRY_OUT
    ]

    return closing

def main():
    if not connect():
        return

    print(f"\n🔍 Buscando todos os trades (magic={MAGIC_NUMBER}, últimos 90 dias)...")
    trades = get_all_trades(days_back=90)

    if not trades:
        print("❌ Nenhum trade encontrado.")
        mt5.shutdown()
        return

    # Agrupa por data
    from collections import defaultdict
    by_date = defaultdict(list)
    for t in trades:
        date = datetime.fromtimestamp(t.time).strftime('%Y-%m-%d')
        by_date[date].append(t)

    print(f"\n{'='*60}")
    print(f"  HISTÓRICO COMPLETO — {len(trades)} trades fechados")
    print(f"{'='*60}")
    print(f"  {'Data':<12} {'Trades':>8} {'Lucro':>12} {'Tickets'}")
    print(f"  {'-'*56}")

    total_profit = 0
    for date in sorted(by_date.keys()):
        day_trades = by_date[date]
        day_profit = sum(t.profit for t in day_trades)
        total_profit += day_profit
        tickets = [str(t.ticket) for t in day_trades[:3]]
        if len(day_trades) > 3:
            tickets.append(f"...+{len(day_trades)-3}")
        print(f"  {date:<12} {len(day_trades):>8} {day_profit:>+12.2f}  {', '.join(tickets)}")

    print(f"  {'-'*56}")
    print(f"  {'TOTAL':<12} {len(trades):>8} {total_profit:>+12.2f}")
    print(f"{'='*60}")

    # Tickets únicos
    tickets = [t.ticket for t in trades]
    duplicados = len(tickets) - len(set(tickets))
    print(f"\n📊 Resumo:")
    print(f"   Total de deals:     {len(trades)}")
    print(f"   Tickets únicos:     {len(set(tickets))}")
    print(f"   Duplicados:         {duplicados}")
    print(f"   Primeiro ticket:    {min(tickets)}")
    print(f"   Último ticket:      {max(tickets)}")
    print(f"   Período:            {sorted(by_date.keys())[0]} → {sorted(by_date.keys())[-1]}")

    winners = [t for t in trades if t.profit > 0]
    print(f"\n   Win rate:           {len(winners)/len(trades)*100:.1f}%")
    print(f"   Lucro total:        ${total_profit:+.2f}")

    mt5.shutdown()

if __name__ == "__main__":
    main()
