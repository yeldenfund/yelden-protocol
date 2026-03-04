"""
mt5_monitor.py — Yelden Protocol Agent Bridge
==============================================
Monitors closed trades from a MetaTrader 5 trading agent
and prepares performance data for the AIAgentRegistry.

Part of: github.com/yeldenfund/yelden-protocol
License: MIT
"""

import MetaTrader5 as mt5
import json
import os
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional

# ── Config ────────────────────────────────────────────────────────────────────

MAGIC_NUMBER   = 975311        # Must match CONFIG['magic_number'] in your bot
LOOKBACK_HOURS = 24            # How far back to check for closed trades
STATE_FILE     = "mt5_monitor_state.json"

# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class ClosedTrade:
    ticket:         int
    symbol:         str
    side:           str       # BUY or SELL
    volume:         float
    open_price:     float
    close_price:    float
    profit:         float
    profit_pct:     float
    r_multiple:     float
    close_reason:   str       # TP, SL, TIMESTOP
    open_time:      str
    close_time:     str
    duration_hours: float
    magic:          int

@dataclass
class AgentPerformance:
    agent_address:     str
    window_start:      str
    window_end:        str
    total_trades:      int
    winning_trades:    int
    win_rate:          float
    total_profit:      float
    sharpe_ratio:      float
    max_drawdown:      float
    avg_r_multiple:    float
    consistency_score: int    # 0-1000, maps to Registry score
    trades:            list

# ── State Management ──────────────────────────────────────────────────────────

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_ticket": 0, "last_check": None}

def save_state(state: dict):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

# ── MT5 Connection ────────────────────────────────────────────────────────────

def connect_mt5(path: Optional[str] = None) -> bool:
    kwargs = {"path": path} if path else {}
    if not mt5.initialize(**kwargs):
        print(f"❌ MT5 connection failed: {mt5.last_error()}")
        return False
    info = mt5.account_info()
    print(f"✅ Connected: {info.login} | {info.server} | Balance: ${info.balance:,.2f}")
    return True

# ── Trade History ─────────────────────────────────────────────────────────────

def get_closed_trades(lookback_hours: int = 24, last_ticket: int = 0) -> list:
    date_from = datetime.now() - timedelta(hours=lookback_hours)
    date_to   = datetime.now()

    deals = mt5.history_deals_get(date_from, date_to)
    if deals is None:
        print(f"⚠️ No deals found: {mt5.last_error()}")
        return []

    closing_deals = [
        d for d in deals
        if d.magic == MAGIC_NUMBER
        and d.entry == mt5.DEAL_ENTRY_OUT
        and d.ticket > last_ticket
    ]

    trades = []
    for deal in closing_deals:
        open_deal, open_order = _find_open_deal_and_order(deal.position_id, date_from, date_to)
        if open_deal is None:
            continue

        symbol       = deal.symbol
        side         = "BUY" if deal.type == mt5.DEAL_TYPE_SELL else "SELL"
        open_price   = open_deal.price
        close_price  = deal.price
        profit       = deal.profit
        volume       = deal.volume
        open_time    = datetime.fromtimestamp(open_deal.time)
        close_time   = datetime.fromtimestamp(deal.time)
        duration_hrs = (close_time - open_time).total_seconds() / 3600
        profit_pct   = (profit / (open_price * volume)) * 100 if open_price > 0 else 0
        sl_price     = getattr(open_order, 'sl', 0.0) if open_order else 0.0
        r_multiple   = _calculate_r_multiple(profit, volume, open_price, sl_price, symbol)
        close_reason = _infer_close_reason(deal, open_price, close_price, side)

        trades.append(ClosedTrade(
            ticket         = deal.ticket,
            symbol         = symbol,
            side           = side,
            volume         = volume,
            open_price     = open_price,
            close_price    = close_price,
            profit         = profit,
            profit_pct     = round(profit_pct, 4),
            r_multiple     = r_multiple,
            close_reason   = close_reason,
            open_time      = open_time.isoformat(),
            close_time     = close_time.isoformat(),
            duration_hours = round(duration_hrs, 2),
            magic          = deal.magic,
        ))

    print(f"✅ Found {len(trades)} new closed trades (SL/TP/timestop)")
    return trades

def _find_open_deal_and_order(position_id: int, date_from: datetime, date_to: datetime):
    """
    Find opening deal AND original order to get real SL price.
    MT5 stores SL in the order, not in the deal.
    """
    # Find opening deal
    all_deals = mt5.history_deals_get(date_from - timedelta(days=30), date_to)
    open_deal = None
    if all_deals:
        for d in all_deals:
            if d.position_id == position_id and d.entry == mt5.DEAL_ENTRY_IN:
                open_deal = d
                break

    if open_deal is None:
        return None, None

    # Find original order to get SL
    all_orders = mt5.history_orders_get(date_from - timedelta(days=30), date_to)
    open_order = None
    if all_orders:
        for o in all_orders:
            if o.position_id == position_id:
                open_order = o
                break

    return open_deal, open_order




def _infer_close_reason(deal, open_price: float, close_price: float, side: str) -> str:
    """
    MT5 doesn't always tag SL/TP explicitly in history.
    Infer from comment and price direction.
    """
    comment = (deal.comment or "").upper()
    if "TP" in comment or "TAKE PROFIT" in comment:
        return "TP"
    if "SL" in comment or "STOP LOSS" in comment:
        return "SL"
    if "BOT_BUYSELL" in comment:
        return "TIMESTOP"
    if side == "BUY":
        return "TP" if close_price > open_price else "SL"
    return "TP" if close_price < open_price else "SL"

def _calculate_r_multiple(profit: float, volume: float, open_price: float, 
                           sl_price: float, symbol: str) -> float:
    if sl_price <= 0 or abs(open_price - sl_price) < 1e-8:
        return 0.0

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        tick_size  = 0.00001
        tick_value = 1.0
    else:
        tick_size  = symbol_info.trade_tick_size
        tick_value = symbol_info.trade_tick_value

    if tick_size <= 0:
        tick_size = 0.00001

    points_risk         = abs(open_price - sl_price) / tick_size
    initial_risk_money  = points_risk * tick_value * volume

    if initial_risk_money <= 0:
        return 0.0

    return round(profit / initial_risk_money, 3)

# ── Performance Calculation ───────────────────────────────────────────────────

def calculate_performance(trades: list, agent_address: str) -> Optional[AgentPerformance]:
    """
    Calculates aggregate performance and maps to Registry score (0-1000).
    """
    if not trades:
        return None

    profits      = [t.profit for t in trades]
    r_multiples  = [t.r_multiple for t in trades]
    winners      = [t for t in trades if t.profit > 0]
    total_profit = sum(profits)
    win_rate     = len(winners) / len(trades)
    avg_r        = sum(r_multiples) / len(r_multiples)

    arr    = np.array(profits)
    sharpe = float((arr.mean() / arr.std()) * (252 ** 0.5)) if arr.std() > 0 else 0.0

    cumulative  = np.cumsum(profits)
    running_max = np.maximum.accumulate(cumulative)
    max_dd      = float((cumulative - running_max).min())

    consistency = _calculate_consistency_score(win_rate, sharpe, avg_r, len(trades))

    return AgentPerformance(
        agent_address     = agent_address,
        window_start      = trades[0].open_time,
        window_end        = trades[-1].close_time,
        total_trades      = len(trades),
        winning_trades    = len(winners),
        win_rate          = round(win_rate, 4),
        total_profit      = round(total_profit, 2),
        sharpe_ratio      = round(sharpe, 4),
        max_drawdown      = round(max_dd, 2),
        avg_r_multiple    = round(avg_r, 4),
        consistency_score = consistency,
        trades            = [asdict(t) for t in trades],
    )

def _calculate_consistency_score(win_rate: float, sharpe: float,
                                   avg_r: float, n_trades: int) -> int:
    """
    Maps performance to Registry score (0-1000).
    Starts at 300 — matches AIAgentRegistry initial score.

    Components:
    - Win rate:     0-300 pts
    - Sharpe:       0-300 pts
    - Positive R:   0-200 pts
    - Trade count:  0-100 pts
    - Floor:        300
    """
    score = 300

    wr_score = min(300, max(0, int((win_rate - 0.30) * 600)))
    score += wr_score

    sharpe_clamped = max(-1.0, min(3.0, sharpe))
    score += int(((sharpe_clamped + 1.0) / 4.0) * 300)

    if avg_r > 0:
        score += min(200, int(avg_r * 100))

    if n_trades >= 50:
        score += 100
    elif n_trades >= 20:
        score += 50
    elif n_trades >= 10:
        score += 25

    return min(1000, max(0, score))

# ── Main ──────────────────────────────────────────────────────────────────────

def run_monitor(agent_address: str, mt5_path: Optional[str] = None) -> Optional[AgentPerformance]:
    """
    Connect to MT5, fetch closed trades, calculate performance.
    Returns AgentPerformance ready for yelden_reporter.py.
    """
    if not connect_mt5(mt5_path):
        return None

    state  = load_state()
    trades = get_closed_trades(
        lookback_hours = LOOKBACK_HOURS,
        last_ticket    = state.get("last_ticket", 0),
    )

    if not trades:
        print("ℹ️ No new trades to report")
        mt5.shutdown()
        return None

    performance = calculate_performance(trades, agent_address)

    if performance:
        last_ticket = max(t.ticket for t in trades)
        save_state({
            "last_ticket": last_ticket,
            "last_check":  datetime.now().isoformat(),
            "last_score":  performance.consistency_score,
        })
        print(f"\n📊 Performance Summary:")
        print(f"   Trades:      {performance.total_trades}")
        print(f"   Win Rate:    {performance.win_rate*100:.1f}%")
        print(f"   Sharpe:      {performance.sharpe_ratio:.2f}")
        print(f"   Max DD:      ${performance.max_drawdown:.2f}")
        print(f"   Avg R:       {performance.avg_r_multiple:.3f}")
        print(f"   Score:       {performance.consistency_score}/1000")

    mt5.shutdown()
    return performance


if __name__ == "__main__":
    AGENT_ADDRESS = "0xYOUR_AGENT_ETHEREUM_ADDRESS"
    MT5_PATH      = r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"

    performance = run_monitor(
        agent_address = AGENT_ADDRESS,
        mt5_path      = MT5_PATH,
    )

    if performance:
        with open("agent_performance.json", "w") as f:
            json.dump(asdict(performance), f, indent=2)
        print(f"\n✅ Saved to agent_performance.json")
        print(f"   Next step: run yelden_reporter.py")
