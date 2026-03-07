"""
trade_history_v2.py — Yelden Protocol
========================================
Análise completa de performance do Markowitz bot.
Métricas profissionais: Sharpe, Sortino, Calmar, Profit Factor,
Expectancy, Recovery Factor, Consistency Score, Streak Analysis,
e muito mais.

Uso: python trade_history_v2.py
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import math
import statistics
from collections import defaultdict

load_dotenv()

MAGIC_NUMBER  = 975311
MT5_PATH      = os.getenv("MT5_PATH", None)
RISK_FREE_RATE = 0.045   # ~4.5% anualizado (US T-bill 2026)
INITIAL_BALANCE = 10_000  # balance inicial estimado para ROI

# ─────────────────────────────────────────────
# CONEXÃO
# ─────────────────────────────────────────────

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
    deals = mt5.history_deals_get(date_from, datetime.now())
    if deals is None:
        print(f"⚠️  No deals: {mt5.last_error()}")
        return []
    return [
        d for d in deals
        if d.magic == MAGIC_NUMBER and d.entry == mt5.DEAL_ENTRY_OUT
    ]

# ─────────────────────────────────────────────
# BLOCO 1 — MÉTRICAS BASE (já existiam)
# ─────────────────────────────────────────────

def base_metrics(trades):
    profits   = [t.profit for t in trades]
    winners   = [p for p in profits if p > 0]
    losers    = [p for p in profits if p < 0]
    total_pnl = sum(profits)
    n         = len(profits)

    win_rate    = len(winners) / n if n else 0
    avg_win     = statistics.mean(winners) if winners else 0
    avg_loss    = abs(statistics.mean(losers)) if losers else 0
    avg_rr      = avg_win / avg_loss if avg_loss else float('inf')
    roi_pct     = (total_pnl / INITIAL_BALANCE) * 100

    return {
        "total_trades"  : n,
        "winners"       : len(winners),
        "losers"        : len(losers),
        "total_pnl"     : total_pnl,
        "win_rate"      : win_rate,
        "avg_win"       : avg_win,
        "avg_loss"      : avg_loss,
        "avg_rr"        : avg_rr,
        "roi_pct"       : roi_pct,
    }

# ─────────────────────────────────────────────
# BLOCO 2 — PROFIT FACTOR & EXPECTANCY
# ─────────────────────────────────────────────

def profit_factor_metrics(trades):
    """
    Profit Factor = Gross Profit / Gross Loss
    Benchmark: >1.5 bom, >2.0 excelente
    
    Expectancy = (WinRate × AvgWin) - (LossRate × AvgLoss)
    Quanto o bot espera ganhar por trade, em média.
    """
    profits = [t.profit for t in trades]
    winners = [p for p in profits if p > 0]
    losers  = [abs(p) for p in profits if p < 0]

    gross_profit = sum(winners)
    gross_loss   = sum(losers)

    profit_factor = gross_profit / gross_loss if gross_loss else float('inf')

    win_rate  = len(winners) / len(profits) if profits else 0
    loss_rate = 1 - win_rate
    avg_win   = statistics.mean(winners) if winners else 0
    avg_loss  = statistics.mean(losers)  if losers  else 0

    expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

    return {
        "gross_profit"  : gross_profit,
        "gross_loss"    : gross_loss,
        "profit_factor" : profit_factor,
        "expectancy"    : expectancy,
    }

# ─────────────────────────────────────────────
# BLOCO 3 — DRAWDOWN (Max DD, Recovery Factor)
# ─────────────────────────────────────────────

def drawdown_metrics(trades):
    """
    Max Drawdown = maior queda pico→vale na equity curve
    Recovery Factor = Total PnL / Max Drawdown
    Calmar Ratio = Annualised Return / Max Drawdown %
    
    Recovery Factor >3 é considerado bom por traders profissionais.
    """
    # constrói equity curve
    profits = [t.profit for t in sorted(trades, key=lambda t: t.time)]
    equity  = [INITIAL_BALANCE]
    for p in profits:
        equity.append(equity[-1] + p)

    peak        = equity[0]
    max_dd_abs  = 0.0
    max_dd_pct  = 0.0
    current_dd  = 0.0

    for val in equity[1:]:
        if val > peak:
            peak = val
        dd     = peak - val
        dd_pct = dd / peak if peak else 0
        if dd > max_dd_abs:
            max_dd_abs = dd
            max_dd_pct = dd_pct
        current_dd = dd

    total_pnl       = equity[-1] - equity[0]
    recovery_factor = total_pnl / max_dd_abs if max_dd_abs else float('inf')

    # período em dias
    if len(trades) >= 2:
        t_sorted   = sorted(trades, key=lambda t: t.time)
        days_total = (t_sorted[-1].time - t_sorted[0].time) / 86400
        days_total = max(days_total, 1)
    else:
        days_total = 1

    annualised_return = (total_pnl / INITIAL_BALANCE) * (365 / days_total)
    calmar_ratio      = annualised_return / max_dd_pct if max_dd_pct else float('inf')

    return {
        "max_dd_abs"        : max_dd_abs,
        "max_dd_pct"        : max_dd_pct * 100,
        "recovery_factor"   : recovery_factor,
        "calmar_ratio"      : calmar_ratio,
        "days_active"       : days_total,
        "annualised_return" : annualised_return * 100,
        "equity_curve"      : equity,
    }

# ─────────────────────────────────────────────
# BLOCO 4 — SHARPE & SORTINO
# ─────────────────────────────────────────────

def risk_adjusted_metrics(trades):
    """
    Sharpe  = (Mean Return - Rf) / StdDev (all returns)
    Sortino = (Mean Return - Rf) / Downside Deviation
    
    Sharpe >1 aceitável, >2 muito bom (hedge funds exigem >3)
    Sortino é mais justo: não penaliza volatilidade positiva.
    """
    profits = [t.profit for t in sorted(trades, key=lambda t: t.time)]
    if len(profits) < 2:
        return {"sharpe": None, "sortino": None}

    # retornos por trade (em % do balance)
    cumulative = INITIAL_BALANCE
    returns    = []
    for p in profits:
        r = p / cumulative
        returns.append(r)
        cumulative += p

    mean_r   = statistics.mean(returns)
    std_r    = statistics.stdev(returns)
    rf_daily = RISK_FREE_RATE / 252   # aproximação diária

    sharpe = (mean_r - rf_daily) / std_r if std_r else float('inf')

    # Sortino: só desvio negativo
    neg_returns   = [r for r in returns if r < rf_daily]
    downside_dev  = math.sqrt(statistics.mean([(r - rf_daily)**2 for r in neg_returns])) if neg_returns else 0
    sortino       = (mean_r - rf_daily) / downside_dev if downside_dev else float('inf')

    # anualizados (por trade count proxy)
    n_per_year  = len(profits) / max((trades[-1].time - trades[0].time) / 86400, 1) * 252
    sharpe_ann  = sharpe  * math.sqrt(n_per_year)
    sortino_ann = sortino * math.sqrt(n_per_year)

    return {
        "sharpe_raw"        : sharpe,
        "sortino_raw"       : sortino,
        "sharpe_annualised" : sharpe_ann,
        "sortino_annualised": sortino_ann,
        "return_std"        : std_r,
        "mean_return_pct"   : mean_r * 100,
    }

# ─────────────────────────────────────────────
# BLOCO 5 — STREAK ANALYSIS
# ─────────────────────────────────────────────

def streak_analysis(trades):
    """
    Analisa sequências de wins/losses.
    Max consecutive wins/losses revela fragilidade psicológica
    e padrões de correlação temporal.
    
    Importante para o Yelden: consistency score depende
    de não ter streaks de losses concentradas.
    """
    profits = [t.profit for t in sorted(trades, key=lambda t: t.time)]
    outcomes = ['W' if p > 0 else 'L' for p in profits]

    max_win_streak  = 0
    max_loss_streak = 0
    cur_win         = 0
    cur_loss        = 0
    all_win_streaks = []
    all_loss_streaks= []

    for o in outcomes:
        if o == 'W':
            cur_win  += 1
            if cur_loss > 0:
                all_loss_streaks.append(cur_loss)
            cur_loss  = 0
            max_win_streak = max(max_win_streak, cur_win)
        else:
            cur_loss += 1
            if cur_win > 0:
                all_win_streaks.append(cur_win)
            cur_win   = 0
            max_loss_streak = max(max_loss_streak, cur_loss)

    if cur_win  > 0: all_win_streaks.append(cur_win)
    if cur_loss > 0: all_loss_streaks.append(cur_loss)

    avg_win_streak  = statistics.mean(all_win_streaks)  if all_win_streaks  else 0
    avg_loss_streak = statistics.mean(all_loss_streaks) if all_loss_streaks else 0

    return {
        "max_win_streak"   : max_win_streak,
        "max_loss_streak"  : max_loss_streak,
        "avg_win_streak"   : avg_win_streak,
        "avg_loss_streak"  : avg_loss_streak,
        "outcome_sequence" : "".join(outcomes[:30]) + ("..." if len(outcomes) > 30 else ""),
    }

# ─────────────────────────────────────────────
# BLOCO 6 — CONSISTÊNCIA TEMPORAL
# ─────────────────────────────────────────────

def temporal_consistency(trades):
    """
    Quantos dias foram profitable vs loss?
    Distribuição de PnL por dia da semana.
    Detecta se o bot tem dias "maus" sistemáticos.
    
    Relevante para o Yelden Consistency Score (Layer 3).
    """
    by_date = defaultdict(list)
    by_weekday = defaultdict(list)

    for t in trades:
        dt = datetime.fromtimestamp(t.time)
        by_date[dt.strftime('%Y-%m-%d')].append(t.profit)
        by_weekday[dt.strftime('%A')].append(t.profit)

    daily_pnls     = [sum(v) for v in by_date.values()]
    profit_days    = sum(1 for p in daily_pnls if p > 0)
    loss_days      = sum(1 for p in daily_pnls if p < 0)
    daily_win_rate = profit_days / len(daily_pnls) if daily_pnls else 0

    # melhor e pior dia da semana
    weekday_avg = {
        day: statistics.mean(pnls)
        for day, pnls in by_weekday.items()
    }

    best_weekday  = max(weekday_avg, key=weekday_avg.get)  if weekday_avg else "N/A"
    worst_weekday = min(weekday_avg, key=weekday_avg.get)  if weekday_avg else "N/A"

    # consistência: std dos PnL diários (menor = mais consistente)
    daily_std = statistics.stdev(daily_pnls) if len(daily_pnls) > 1 else 0

    return {
        "trading_days"       : len(by_date),
        "profit_days"        : profit_days,
        "loss_days"          : loss_days,
        "daily_win_rate"     : daily_win_rate,
        "daily_pnl_std"      : daily_std,
        "best_weekday"       : f"{best_weekday} (avg ${weekday_avg.get(best_weekday, 0):.2f})",
        "worst_weekday"      : f"{worst_weekday} (avg ${weekday_avg.get(worst_weekday, 0):.2f})",
        "weekday_breakdown"  : weekday_avg,
    }

# ─────────────────────────────────────────────
# BLOCO 7 — DISTRIBUIÇÃO DE RETORNOS
# ─────────────────────────────────────────────

def return_distribution(trades):
    """
    Skewness e Kurtosis dos retornos.
    
    Skewness positiva = mais wins pequenos + wins grandes ocasionais (bom)
    Skewness negativa = wins pequenos + losses grandes (perigoso)
    
    Kurtosis alta = fat tails = eventos extremos mais prováveis do que
    uma distribuição normal sugere. Sharpe ratio subestima o risco neste caso.
    
    95% VaR: qual é o pior resultado esperado em 95% dos dias?
    """
    profits = [t.profit for t in trades]
    if len(profits) < 4:
        return {}

    mean_p  = statistics.mean(profits)
    std_p   = statistics.stdev(profits)
    n       = len(profits)

    # Skewness
    skewness = sum(((p - mean_p) / std_p) ** 3 for p in profits) * n / ((n-1) * (n-2)) if std_p else 0

    # Kurtosis (excess)
    if n > 3 and std_p:
        kurtosis = (
            n * (n+1) / ((n-1) * (n-2) * (n-3)) *
            sum(((p - mean_p) / std_p) ** 4 for p in profits)
        ) - 3 * (n-1)**2 / ((n-2) * (n-3))
    else:
        kurtosis = 0

    # VaR 95% (paramétrico simples)
    var_95 = mean_p - 1.645 * std_p

    # CVaR 95% (média dos piores 5%)
    sorted_p    = sorted(profits)
    cutoff_idx  = max(1, int(0.05 * n))
    cvar_95     = statistics.mean(sorted_p[:cutoff_idx])

    # Percentis
    sorted_p = sorted(profits)
    p10 = sorted_p[int(0.10 * n)]
    p25 = sorted_p[int(0.25 * n)]
    p75 = sorted_p[int(0.75 * n)]
    p90 = sorted_p[int(0.90 * n)]

    return {
        "mean_trade"  : mean_p,
        "std_trade"   : std_p,
        "skewness"    : skewness,
        "kurtosis"    : kurtosis,
        "var_95"      : var_95,
        "cvar_95"     : cvar_95,
        "p10"         : p10,
        "p25"         : p25,
        "p75"         : p75,
        "p90"         : p90,
        "best_trade"  : max(profits),
        "worst_trade" : min(profits),
    }

# ─────────────────────────────────────────────
# BLOCO 8 — YELDEN SCORE (F2 + 60-day decay)
# ─────────────────────────────────────────────

def yelden_f2_score(trades, balance=10650.33):
    """
    Fórmula proprietária Yelden Protocol.
    F2 score por run + média ponderada com decay temporal.
    
    Score 0-1000.
    """
    by_date = defaultdict(list)
    now = datetime.now()

    for t in trades:
        dt = datetime.fromtimestamp(t.time).strftime('%Y-%m-%d')
        by_date[dt].append(t)

    # Agrupa em "runs" por data
    run_scores  = []
    run_weights = []

    for date_str in sorted(by_date.keys()):
        day_trades  = by_date[date_str]
        day_profits = [t.profit for t in day_trades]
        n           = len(day_trades)

        if n == 0:
            continue

        winners   = [p for p in day_profits if p > 0]
        losers    = [p for p in day_profits if p < 0]
        win_rate  = len(winners) / n

        # Métricas base do run
        avg_win   = statistics.mean(winners) if winners else 0
        avg_loss  = abs(statistics.mean(losers)) if losers else 1e-9
        avg_rr    = avg_win / avg_loss
        total_pnl = sum(day_profits)
        ret_pct   = total_pnl / balance

        # Sharpe simplificado por run (se > 1 trade)
        if n > 1:
            std_day = statistics.stdev(day_profits)
            sharpe  = statistics.mean(day_profits) / std_day if std_day else 1.0
        else:
            sharpe = 1.0

        # F2 score (0-1000)
        base_score = (
            win_rate       * 400 +      # 40% — win rate
            min(avg_rr, 3) / 3 * 200 +  # 20% — R:R (cap 3)
            min(max(sharpe, -1), 3) / 3 * 200 +  # 20% — Sharpe
            min(abs(ret_pct) * 10, 1) * 200       # 20% — return magnitude
        )
        # penalidade se retorno negativo
        if total_pnl < 0:
            base_score *= 0.3

        base_score = max(0, min(1000, base_score))

        # decay temporal: half-life 60 dias
        date_obj  = datetime.strptime(date_str, '%Y-%m-%d')
        days_ago  = (now - date_obj).days
        decay     = math.exp(-0.693 * days_ago / 60)
        weight    = n * decay

        run_scores.append(base_score)
        run_weights.append(weight)

    if not run_weights:
        return {"accumulated_score": 0, "runs": 0}

    accumulated = sum(s * w for s, w in zip(run_scores, run_weights)) / sum(run_weights)

    return {
        "accumulated_score" : round(accumulated, 1),
        "runs"              : len(run_scores),
        "avg_run_score"     : round(statistics.mean(run_scores), 1),
        "last_run_score"    : round(run_scores[-1], 1) if run_scores else 0,
    }

# ─────────────────────────────────────────────
# OUTPUT
# ─────────────────────────────────────────────

def print_section(title):
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print(f"{'═'*60}")

def rating(value, thresholds, labels):
    """Devolve label com base em thresholds crescentes."""
    for t, l in zip(thresholds, labels):
        if value < t:
            return l
    return labels[-1]

def main():
    if not connect():
        return

    print(f"\n🔍 Buscando trades (magic={MAGIC_NUMBER}, últimos 90 dias)...")
    trades = get_all_trades(days_back=90)

    if not trades:
        print("❌ Nenhum trade encontrado.")
        mt5.shutdown()
        return

    trades_sorted = sorted(trades, key=lambda t: t.time)
    t_first = datetime.fromtimestamp(trades_sorted[0].time).strftime('%Y-%m-%d')
    t_last  = datetime.fromtimestamp(trades_sorted[-1].time).strftime('%Y-%m-%d')

    # ── calcula tudo ──
    base   = base_metrics(trades)
    pf     = profit_factor_metrics(trades)
    dd     = drawdown_metrics(trades_sorted)
    ra     = risk_adjusted_metrics(trades_sorted)
    streak = streak_analysis(trades_sorted)
    tc     = temporal_consistency(trades_sorted)
    dist   = return_distribution(trades_sorted)
    yelden = yelden_f2_score(trades_sorted)

    # ── BLOCO 1: RESUMO GERAL ──
    print_section("📊 RESUMO GERAL")
    print(f"  Período           : {t_first} → {t_last} ({dd['days_active']:.0f} dias)")
    print(f"  Total de trades   : {base['total_trades']}")
    print(f"  Winners / Losers  : {base['winners']} / {base['losers']}")
    print(f"  PnL Total         : ${base['total_pnl']:+.2f}")
    print(f"  ROI               : {base['roi_pct']:+.2f}%")
    print(f"  Retorno anualizado: {dd['annualised_return']:+.1f}%")

    # ── BLOCO 2: RENTABILIDADE ──
    print_section("💰 RENTABILIDADE")
    pf_rating = rating(pf['profit_factor'], [1.0, 1.3, 1.5, 2.0], ["❌ Negativo","⚠️ Fraco","🟡 Aceitável","🟢 Bom","🔵 Excelente"])
    ex_rating = rating(pf['expectancy'], [-1, 0, 5, 15], ["❌ Negativo","⚠️ Marginal","🟡 Ok","🟢 Bom","🔵 Excelente"])

    print(f"  Win Rate          : {base['win_rate']*100:.1f}%")
    print(f"  Avg Win           : ${base['avg_win']:+.2f}")
    print(f"  Avg Loss          : $-{base['avg_loss']:.2f}")
    print(f"  Avg R:R           : {base['avg_rr']:.2f}:1")
    print(f"  Profit Factor     : {pf['profit_factor']:.2f}  {pf_rating}")
    print(f"  Expectancy/trade  : ${pf['expectancy']:+.2f}  {ex_rating}")
    print(f"  Gross Profit      : ${pf['gross_profit']:+.2f}")
    print(f"  Gross Loss        : $-{pf['gross_loss']:.2f}")

    # ── BLOCO 3: RISCO ──
    print_section("⚠️  RISCO & DRAWDOWN")
    dd_rating  = rating(dd['max_dd_pct'], [2, 5, 10, 20], ["🔵 Mínimo","🟢 Baixo","🟡 Moderado","🟠 Alto","❌ Crítico"])
    rf_rating  = rating(dd['recovery_factor'], [1, 2, 3, 5], ["❌ Fraco","⚠️ Baixo","🟡 Aceitável","🟢 Bom","🔵 Excelente"])
    cal_rating = rating(dd['calmar_ratio'], [0.5, 1.0, 2.0, 3.0], ["❌ Fraco","⚠️ Baixo","🟡 Ok","🟢 Bom","🔵 Excelente"])

    print(f"  Max Drawdown $    : ${dd['max_dd_abs']:.2f}  {dd_rating}")
    print(f"  Max Drawdown %    : {dd['max_dd_pct']:.2f}%")
    print(f"  Recovery Factor   : {dd['recovery_factor']:.2f}  {rf_rating}")
    print(f"  Calmar Ratio      : {dd['calmar_ratio']:.2f}  {cal_rating}")

    # ── BLOCO 4: SHARPE & SORTINO ──
    print_section("📐 RISCO AJUSTADO (Sharpe / Sortino)")
    if ra.get('sharpe_annualised') is not None:
        sh_rating = rating(ra['sharpe_annualised'], [0, 0.5, 1.0, 2.0], ["❌ Negativo","⚠️ Fraco","🟡 Aceitável","🟢 Bom","🔵 Excelente"])
        so_rating = rating(ra['sortino_annualised'], [0, 0.5, 1.5, 3.0], ["❌ Negativo","⚠️ Fraco","🟡 Aceitável","🟢 Bom","🔵 Excelente"])

        print(f"  Sharpe (anual.)   : {ra['sharpe_annualised']:.3f}  {sh_rating}")
        print(f"  Sortino (anual.)  : {ra['sortino_annualised']:.3f}  {so_rating}")
        print(f"  Sharpe (raw/trd)  : {ra['sharpe_raw']:.3f}")
        print(f"  Return StdDev     : {ra['return_std']*100:.3f}%/trade")
        print(f"  Mean Return       : {ra['mean_return_pct']:+.3f}%/trade")
    else:
        print("  ⚠️  Dados insuficientes para Sharpe/Sortino")

    # ── BLOCO 5: DISTRIBUIÇÃO ──
    print_section("📈 DISTRIBUIÇÃO DE RETORNOS")
    if dist:
        sk_label = "positiva ✅ (wins grandes ocasionais)" if dist['skewness'] > 0 else "negativa ⚠️ (losses grandes ocasionais)"
        kt_label = "fat tails ⚠️" if dist['kurtosis'] > 1 else "normal 🟢"

        print(f"  Melhor trade      : ${dist['best_trade']:+.2f}")
        print(f"  Pior trade        : ${dist['worst_trade']:+.2f}")
        print(f"  Média por trade   : ${dist['mean_trade']:+.2f}")
        print(f"  StdDev por trade  : ${dist['std_trade']:.2f}")
        print(f"  Skewness          : {dist['skewness']:+.3f}  ({sk_label})")
        print(f"  Kurtosis (excess) : {dist['kurtosis']:+.3f}  ({kt_label})")
        print(f"  VaR 95% (param.)  : ${dist['var_95']:+.2f}  (pior esperado 95% dos trades)")
        print(f"  CVaR 95%          : ${dist['cvar_95']:+.2f}  (média dos 5% piores trades)")
        print(f"  Percentis P10/P25 : ${dist['p10']:+.2f} / ${dist['p25']:+.2f}")
        print(f"  Percentis P75/P90 : ${dist['p75']:+.2f} / ${dist['p90']:+.2f}")

    # ── BLOCO 6: STREAK ANALYSIS ──
    print_section("🔗 STREAK ANALYSIS")
    print(f"  Max wins seguidos : {streak['max_win_streak']}")
    print(f"  Max losses seguid.: {streak['max_loss_streak']}")
    print(f"  Avg win streak    : {streak['avg_win_streak']:.1f}")
    print(f"  Avg loss streak   : {streak['avg_loss_streak']:.1f}")
    print(f"  Sequência (30)    : {streak['outcome_sequence']}")

    # ── BLOCO 7: CONSISTÊNCIA TEMPORAL ──
    print_section("📅 CONSISTÊNCIA TEMPORAL")
    print(f"  Dias com trades   : {tc['trading_days']}")
    print(f"  Dias lucrativos   : {tc['profit_days']}  ({tc['daily_win_rate']*100:.1f}%)")
    print(f"  Dias negativos    : {tc['loss_days']}")
    print(f"  Volatilidade/dia  : ${tc['daily_pnl_std']:.2f} (StdDev PnL diário)")
    print(f"  Melhor dia semana : {tc['best_weekday']}")
    print(f"  Pior dia semana   : {tc['worst_weekday']}")
    print(f"\n  PnL médio por dia da semana:")
    for day, avg in sorted(tc['weekday_breakdown'].items()):
        bar = "█" * int(abs(avg) / 5)
        sign = "+" if avg >= 0 else "-"
        print(f"    {day:<12} {sign}${abs(avg):6.2f}  {bar}")

    # ── BLOCO 8: YELDEN SCORE ──
    print_section("🏆 YELDEN SCORE (F2 + 60-day decay)")
    y = yelden
    tier = (
        "🔵 Platinum" if y['accumulated_score'] >= 850 else
        "🟡 Gold"     if y['accumulated_score'] >= 700 else
        "⚪ Silver"   if y['accumulated_score'] >= 500 else
        "🟤 Bronze"   if y['accumulated_score'] >= 300 else
        "⬜ Unranked"
    )
    print(f"  Score Acumulado   : {y['accumulated_score']:.1f}/1000  {tier}")
    print(f"  Runs analisados   : {y['runs']}")
    print(f"  Score médio/run   : {y['avg_run_score']:.1f}")
    print(f"  Último run score  : {y['last_run_score']:.1f}")

    # ── BLOCO 9: DIAGNÓSTICO ──
    print_section("🔬 DIAGNÓSTICO FINAL")

    issues   = []
    strengths= []

    if base['win_rate'] >= 0.60:
        strengths.append(f"Win rate forte ({base['win_rate']*100:.1f}%)")
    if pf['profit_factor'] >= 1.5:
        strengths.append(f"Profit factor sólido ({pf['profit_factor']:.2f})")
    if dd['max_dd_pct'] < 5:
        strengths.append(f"Drawdown baixo ({dd['max_dd_pct']:.1f}%)")
    if dd['recovery_factor'] >= 3:
        strengths.append(f"Recovery factor excelente ({dd['recovery_factor']:.1f})")
    if dist and dist['skewness'] > 0:
        strengths.append("Distribuição com skewness positiva")
    if tc['daily_win_rate'] >= 0.60:
        strengths.append(f"Maioria dos dias lucrativos ({tc['daily_win_rate']*100:.0f}%)")

    if pf['profit_factor'] < 1.5:
        issues.append(f"Profit factor abaixo de 1.5 (actual: {pf['profit_factor']:.2f})")
    if base['avg_rr'] < 1.0:
        issues.append(f"R:R < 1.0 — wins menores que losses em média")
    if dd['max_dd_pct'] > 10:
        issues.append(f"Max drawdown elevado ({dd['max_dd_pct']:.1f}%)")
    if streak['max_loss_streak'] >= 5:
        issues.append(f"Streak de {streak['max_loss_streak']} losses consecutivos detectada")
    if dist and dist['kurtosis'] > 2:
        issues.append(f"Kurtosis alta ({dist['kurtosis']:.1f}) — fat tails, Sharpe subestima risco")
    if dist and dist['skewness'] < -0.5:
        issues.append("Skewness negativa — losses grandes ocasionais")

    print(f"\n  ✅ Pontos fortes:")
    for s in strengths:
        print(f"     • {s}")

    print(f"\n  ⚠️  Pontos de atenção:")
    for i in issues:
        print(f"     • {i}")

    if not issues:
        print("     • Nenhum problema crítico detectado neste período.")

    # ── HISTÓRICO POR DATA ──
    print_section("📋 HISTÓRICO POR DATA")
    by_date = defaultdict(list)
    for t in trades:
        date = datetime.fromtimestamp(t.time).strftime('%Y-%m-%d')
        by_date[date].append(t)

    print(f"  {'Data':<12} {'Trades':>7} {'Lucro':>10} {'Win%':>7} {'Tickets'}")
    print(f"  {'-'*56}")
    total_p = 0
    for date in sorted(by_date.keys()):
        day_trades  = by_date[date]
        day_profit  = sum(t.profit for t in day_trades)
        day_wr      = sum(1 for t in day_trades if t.profit > 0) / len(day_trades) * 100
        total_p    += day_profit
        tickets     = [str(t.ticket) for t in day_trades[:3]]
        if len(day_trades) > 3:
            tickets.append(f"+{len(day_trades)-3}")
        emoji = "🟢" if day_profit > 0 else "🔴"
        print(f"  {emoji} {date:<10} {len(day_trades):>7} {day_profit:>+10.2f} {day_wr:>6.0f}%  {', '.join(tickets)}")

    print(f"  {'-'*56}")
    print(f"  {'TOTAL':<12} {base['total_trades']:>7} {total_p:>+10.2f}")

    print(f"\n{'═'*60}\n")
    mt5.shutdown()

if __name__ == "__main__":
    main()
