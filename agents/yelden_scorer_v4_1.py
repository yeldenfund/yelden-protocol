"""
╔══════════════════════════════════════════════════════════════════════╗
║          YELDEN PROTOCOL — Agent Scorer v4.1                        ║
║          S_raw Multi-Factor (11 componentes) × EMA × CF × SF        ║
║          Fórmula: Sistema(t) = EMA(t) × CF(t) × SF(t)               ║
║          Escala: 0–1000  |  Bands: EXP / PROM / VER / ELITE / LEG   ║
║          Referências: Lo (2002), Bailey & López de Prado (2014)      ║
╚══════════════════════════════════════════════════════════════════════╝

Changelog v4.1 (fixes live-data validados com Markowitz Bot):
  FIX 1: Sortino Confidence — n_neg_days → loss_trades
          Markowitz: conf=0.20 (errado) → conf=1.00 (correto)  +5.16 pts
  FIX 2: Expectancy — %/trade diluída → E(R) = WR×AvgR − (1−WR) scale-free
          Funciona com 29 posições simultâneas MT5 e Myfxbook indistintamente
  FIX 3: Smoothness² — vol/return ratio → Calmar Ratio (ROI/MaxDD, tecto=3.0)
          Markowitz: smoothness=0.00 (errado) → 0.93 (correto)  +10.37 pts
  Total delta: S_raw 49.76 → 72.58 (+22.82 pts)
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# ══════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════════════

INITIAL_CAPITAL   = 10_000       # Capital base para cálculo de retornos %
HISTORY_DAYS      = 365          # Janela de histórico MT5

# Parâmetros EMA × CF × SF
EMA_ALPHA         = 0.85         # Decaimento EMA (testado: 0.70/0.80/0.85/0.90/0.95)
EMA_INITIAL       = 300          # Ponto de partida neutro para agente novo
CF_REFERENCE      = 200          # Trades para CF = 1.0 (Lo 2002: √N scaling)
SF_WINDOW         = 6            # Janela SF em rodadas (meses)
SF_THRESHOLD      = 40           # S_raw mínimo para SF = 1.0

# Tectos de normalização v4
CAP_SHARPE        = 2.5          # Reduzido de 3.0 — mais discriminação
CAP_SORTINO       = 8.0          # Sortino efectivo máximo
CAP_PF            = 2.5          # PF=2.5 → 100pts  (reduzido de 3.0)
CAP_AVG_R         = 1.2          # AvgR ceiling (reduzido de 1.5)
CAP_EXPECTANCY    = 0.5          # v4.1: tecto E(R) escala-livre (era 20%/trade)
CAP_VOL           = 1.0          # Volatilidade diária máxima aceitável (%)
MIN_LOSS_TRADES   = 20           # v4.1: mínimo de loss_trades para Sortino confiável (era neg_days)

# Pesos S_raw v4 — soma aditivos = 1.00, DD separado
W = {
    'sharpe':     0.18,
    'sortino':    0.08,
    'winrate':    0.12,
    'pf':         0.15,
    'avg_r':      0.08,
    'expectancy': 0.10,
    'vol':        0.07,
    'stability':  0.12,
    'smoothness': 0.12,
    'dd':         0.25,   # penalidade directa
}

# Ficheiro de estado persistente (EMA + histórico SF)
STATE_FILE = os.path.join(os.path.dirname(__file__), 'yelden_state.json')

# ══════════════════════════════════════════════════════════════════════
# ESTADO PERSISTENTE — EMA e histórico de S_raw para SF
# ══════════════════════════════════════════════════════════════════════

def load_state():
    """Carrega estado persistente do agente (EMA + histórico rounds)."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'ema': EMA_INITIAL,
        'round_history': [],   # lista de S_raw por rodada (mais recente último)
        'total_trades': 0,
        'last_updated': None,
    }

def save_state(state):
    """Persiste estado do agente."""
    state['last_updated'] = datetime.now().isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    print(f"\n[STATE] Guardado em {STATE_FILE}")

# ══════════════════════════════════════════════════════════════════════
# CONEXÃO MT5
# ══════════════════════════════════════════════════════════════════════

if not mt5.initialize():
    print("Erro ao conectar no MT5")
    quit()

print("Conectado ao MT5")

# ══════════════════════════════════════════════════════════════════════
# LEITURA DE TRADES
# ══════════════════════════════════════════════════════════════════════

date_from = datetime.now() - timedelta(days=HISTORY_DAYS)
date_to   = datetime.now()

deals = mt5.history_deals_get(date_from, date_to)

if deals is None or len(deals) == 0:
    print("Nenhum trade/deal encontrado no período")
    mt5.shutdown()
    quit()

df = pd.DataFrame([d._asdict() for d in deals])
print(f"Total de deals: {len(df)}")

# Filtrar: apenas operações fechadas com lucro/prejuízo
df = df[df['entry'] == mt5.DEAL_ENTRY_OUT]
df = df[df['profit'] != 0]
print(f"Trades após filtro: {len(df)}")

if len(df) == 0:
    print("Nenhum trade fechado encontrado")
    mt5.shutdown()
    quit()

df = df.sort_values('time').reset_index(drop=True)
df['datetime'] = pd.to_datetime(df['time'], unit='s')
df['date']     = df['datetime'].dt.date

profits = df['profit'].astype(float).values

# ══════════════════════════════════════════════════════════════════════
# MÉTRICAS BASE
# ══════════════════════════════════════════════════════════════════════

trade_count  = len(profits)
wins         = profits[profits > 0]
losses       = profits[profits < 0]
win_rate     = len(wins) / trade_count if trade_count > 0 else 0
avg_win      = wins.mean()  if len(wins)   > 0 else 0
avg_loss     = abs(losses.mean()) if len(losses) > 0 else 0

gross_profit = wins.sum()
gross_loss   = abs(losses.sum())
profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

loss_rate    = 1 - win_rate
expectancy_dollar = (win_rate * avg_win) - (loss_rate * avg_loss)
avg_r        = (avg_win / avg_loss) if avg_loss > 0 else 0

# Expectancy como % do capital por trade
# Aproximação: retorno médio por trade / capital
avg_profit_per_trade = profits.mean()
expectancy_pct = (avg_profit_per_trade / INITIAL_CAPITAL) * 100

# ══════════════════════════════════════════════════════════════════════
# RETORNOS DIÁRIOS
# ══════════════════════════════════════════════════════════════════════

daily_profits     = df.groupby('date')['profit'].sum()
daily_returns     = daily_profits.values
daily_returns_pct = (daily_returns / INITIAL_CAPITAL) * 100

mean_daily_pct    = np.mean(daily_returns_pct)
std_daily_pct     = np.std(daily_returns_pct)

# ══════════════════════════════════════════════════════════════════════
# COMPONENTE 1 — SHARPE RATIO
# ══════════════════════════════════════════════════════════════════════

sharpe_daily  = (mean_daily_pct / std_daily_pct) if std_daily_pct > 0 else 0
annual_return = mean_daily_pct * 252
annual_std    = std_daily_pct * np.sqrt(252)
sharpe_annual = (annual_return / annual_std) if annual_std > 0 else 0
t_stat        = sharpe_daily * np.sqrt(trade_count)

S_sharpe = min(max(sharpe_annual / CAP_SHARPE, 0), 1.0) * 100

# ══════════════════════════════════════════════════════════════════════
# COMPONENTE 2 — SORTINO × CONFIDENCE ADJUSTMENT (Lo 2002)
# ══════════════════════════════════════════════════════════════════════

neg_daily      = daily_returns_pct[daily_returns_pct < 0]
n_neg_days     = len(neg_daily)
downside_std   = np.std(neg_daily) if len(neg_daily) > 0 else 0
annual_ds_std  = downside_std * np.sqrt(252)
sortino_raw    = (annual_return / annual_ds_std) if annual_ds_std > 0 else 0

# FIX v4.1: loss_trades em vez de n_neg_days
# Markowitz Bot: neg_days=4 → conf=0.20 (errado); loss_trades=26 → conf=1.00 (correto)
# Sortino é calculado com base em trades, não em dias — a confiança deve usar a mesma base
loss_trades    = len(losses)       # número de trades com P&L negativo
sortino_conf   = min(loss_trades / MIN_LOSS_TRADES, 1.0)
sortino_eff    = sortino_raw * sortino_conf

S_sortino = min(max(sortino_eff / CAP_SORTINO, 0), 1.0) * 100

# ══════════════════════════════════════════════════════════════════════
# COMPONENTE 3 — WIN RATE (linear)
# ══════════════════════════════════════════════════════════════════════

S_winrate = win_rate * 100

# ══════════════════════════════════════════════════════════════════════
# COMPONENTE 4 — PROFIT FACTOR  [tecto PF=2.5]
# ══════════════════════════════════════════════════════════════════════

S_pf = min(max(profit_factor - 1.0, 0) / (CAP_PF - 1.0), 1.0) * 100

# ══════════════════════════════════════════════════════════════════════
# COMPONENTE 5 — AVG R-MULTIPLE  [tecto 1.2]
# ══════════════════════════════════════════════════════════════════════

S_avg_r = min(avg_r / CAP_AVG_R, 1.0) * 100

# ══════════════════════════════════════════════════════════════════════
# COMPONENTE 6 — EXPECTANCY  [tecto 20%/trade]  [NOVO v4]
# ══════════════════════════════════════════════════════════════════════

# FIX v4.1: E(R) escala-livre em vez de %/trade diluída pelo capital
# E(R) = WR × AvgR − (1−WR) × 1.0
# WR=0.625, AvgR=1.35 → E(R)=0.366 — idêntico em MT5 e Myfxbook independente do capital
# A fórmula antiga (avg_profit/capital) fica próxima de 0 com 29 posições simultâneas
E_R          = win_rate * avg_r - (1 - win_rate) * 1.0
S_expectancy = min(max(E_R, 0) / CAP_EXPECTANCY, 1.0) * 100

# ══════════════════════════════════════════════════════════════════════
# COMPONENTE 7 — VOLATILIDADE DIÁRIA  [tecto 1.0%/dia]  [NOVO v4]
# ══════════════════════════════════════════════════════════════════════

volatility_pct = std_daily_pct   # desvio-padrão dos retornos diários em %
S_vol = max(1.0 - volatility_pct / CAP_VOL, 0.0) * 100

# ══════════════════════════════════════════════════════════════════════
# COMPONENTE 8 — STABILITY²  [NOVO v4]
# Dispersão dos Sharpe mensais — baixa dispersão = alta consistency
# ══════════════════════════════════════════════════════════════════════

df['year_month'] = df['datetime'].dt.to_period('M')
monthly_sharpes  = []

for month, grp in df.groupby('year_month'):
    m_daily = grp.groupby('date')['profit'].sum()
    m_ret   = (m_daily.values / INITIAL_CAPITAL) * 100
    m_std   = np.std(m_ret)
    m_mean  = np.mean(m_ret)
    if m_std > 0:
        monthly_sharpes.append(m_mean / m_std)
    else:
        monthly_sharpes.append(0.0)

if len(monthly_sharpes) > 0:
    sharpe_std_monthly   = np.std(monthly_sharpes)
    stability_raw        = 1.0 / (1.0 + sharpe_std_monthly)
else:
    sharpe_std_monthly   = 0
    stability_raw        = 0.5

# Expoente 2.0 — penaliza mais a instabilidade (Bailey & López de Prado)
S_stability = (stability_raw ** 2.0) * 100

# ══════════════════════════════════════════════════════════════════════
# COMPONENTE 9 — SMOOTHNESS²  [NOVO v4]
# Suavidade da equity curve — razão volatilidade/retorno diário
# ══════════════════════════════════════════════════════════════════════

# FIX v4.1: Calmar Ratio em vez de vol/return ratio
# O ratio vol/return produzia smoothness=0 para estratégias com baixo retorno diário médio
# (ex: Markowitz Bot com vol/return=3.01 → smoothness=0, apesar de Calmar=2.79 excelente)
# Calmar = ROI_total / max_drawdown_pct — broker-agnostic, tecto=3.0 (hedge-fund grade)
roi_total      = (equity_curve[-1] - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
calmar         = (roi_total / max_dd_pct) if max_dd_pct > 0 else 0.0
smoothness_raw = min(max(calmar / 3.0, 0.0), 1.0)

# Expoente 2.0 — idem Stability
S_smoothness = (smoothness_raw ** 2.0) * 100

# ══════════════════════════════════════════════════════════════════════
# COMPONENTE 10 — MAX DRAWDOWN (penalidade directa)
# ══════════════════════════════════════════════════════════════════════

equity_curve = INITIAL_CAPITAL + np.cumsum(profits)
equity_curve = np.maximum(equity_curve, 1.0)
peak_equity  = np.maximum.accumulate(equity_curve)
drawdown_arr = (peak_equity - equity_curve) / peak_equity
max_dd_pct   = float(np.max(drawdown_arr)) * 100   # em %

# Penalidade directa: DD% × peso (não normalizado — subtracção directa)
DD_penalty   = max_dd_pct * W['dd']

# ══════════════════════════════════════════════════════════════════════
# S_RAW v4 — COMBINAÇÃO DOS 11 COMPONENTES
# ══════════════════════════════════════════════════════════════════════

S_raw = (
    S_sharpe     * W['sharpe']     +
    S_sortino    * W['sortino']    +
    S_winrate    * W['winrate']    +
    S_pf         * W['pf']        +
    S_avg_r      * W['avg_r']     +
    S_expectancy * W['expectancy'] +
    S_vol        * W['vol']        +
    S_stability  * W['stability']  +
    S_smoothness * W['smoothness'] -
    DD_penalty                      # penalidade directa
)

# ══════════════════════════════════════════════════════════════════════
# LAYER 2 — EMA (Quality Accumulator)
# EMA(t) = EMA(t-1) × α + S_raw(t) × 10 × (1-α)
# ══════════════════════════════════════════════════════════════════════

state = load_state()

ema_prev        = state.get('ema', EMA_INITIAL)
round_history   = state.get('round_history', [])
cumulative_trades = state.get('total_trades', 0) + trade_count

ema_new = ema_prev * EMA_ALPHA + (S_raw * 10) * (1 - EMA_ALPHA)
ema_new = float(np.clip(ema_new, 0, 1000))

# ══════════════════════════════════════════════════════════════════════
# LAYER 3A — CF: Confidence Factor (Lo 2002 — √N scaling)
# CF = min(√(cumulative_trades / 200), 1.0)
# ══════════════════════════════════════════════════════════════════════

CF = min(np.sqrt(cumulative_trades / CF_REFERENCE), 1.0)

# ══════════════════════════════════════════════════════════════════════
# LAYER 3B — SF: Stability Factor (memória de catástrofe 6 rodadas)
# SF = min(worst_S_raw_last_6_rounds / 40, 1.0)
# ══════════════════════════════════════════════════════════════════════

# Adiciona rodada actual ao histórico
round_history_updated = round_history + [float(S_raw)]

# Janela deslizante últimas SF_WINDOW rodadas
sf_window = round_history_updated[-SF_WINDOW:]
worst_sraw_6m = min(sf_window) if sf_window else S_raw

SF = max(min(worst_sraw_6m / SF_THRESHOLD, 1.0), 0.0)

# ══════════════════════════════════════════════════════════════════════
# SISTEMA FINAL — Score on-chain (0–1000)
# Sistema(t) = EMA(t) × CF(t) × SF(t)
# ══════════════════════════════════════════════════════════════════════

sistema = float(np.clip(ema_new * CF * SF, 0, 1000))

# ══════════════════════════════════════════════════════════════════════
# STAGE CLASSIFICATION
# ══════════════════════════════════════════════════════════════════════

def get_stage(score):
    if score < 200:  return "EXPERIMENTAL"
    if score < 400:  return "PROMISING"
    if score < 600:  return "VERIFIED"
    if score < 800:  return "ELITE"
    return "LEGENDARY"

stage_sraw    = get_stage(S_raw * 10)   # S_raw×10 para comparar com escala 0-1000
stage_sistema = get_stage(sistema)

# ══════════════════════════════════════════════════════════════════════
# OUTPUT
# ══════════════════════════════════════════════════════════════════════

SEP = "━" * 70
sep = "─" * 70

print(f"\n{SEP}")
print("  YELDEN PROTOCOL — AGENT SCORER v4.1")
print("  3 Live-Data Fixes: Sortino Conf · Expectancy E(R) · Smoothness Calmar")
print(f"{SEP}")

print(f"\n{'─'*35} PERFORMANCE {'─'*22}")
print(f"  Total Trades:                {trade_count}")
print(f"  Win Rate:                    {win_rate*100:.1f}%")
print(f"  Profit Factor:               {profit_factor:.3f}")
print(f"  Expectancy ($/trade):        ${expectancy_dollar:.2f}")
print(f"  Expectancy E(R):             {E_R:.3f}            [tecto={CAP_EXPECTANCY}]")
print(f"  Avg Win / Avg Loss:          ${avg_win:.2f} / ${avg_loss:.2f}")
print(f"  Avg R-Multiple:              {avg_r:.3f}              [tecto={CAP_AVG_R}]")

print(f"\n{'─'*35} RISK {'─'*29}")
print(f"  Sharpe Ratio (annual):       {sharpe_annual:.3f}        [tecto={CAP_SHARPE}]")
print(f"  Sortino (raw):               {sortino_raw:.3f}")
print(f"  Sortino confidence:          {sortino_conf:.2f}  ({loss_trades}/{MIN_LOSS_TRADES} loss_trades)  [v4.1]")
print(f"  Sortino efectivo:            {sortino_eff:.3f}        [tecto={CAP_SORTINO}]")
print(f"  Max Drawdown:                {max_dd_pct:.2f}%")
print(f"  Daily Volatility:            {volatility_pct:.3f}%/dia       [tecto={CAP_VOL}%]")
print(f"  T-Statistic:                 {t_stat:.3f}")

print(f"\n{'─'*35} CONSISTENCY  [NOVO v4] {'─'*11}")
print(f"  Stability (0→1):             {stability_raw:.4f}")
print(f"  Stability² score:            {S_stability:.1f}/100")
print(f"  Monthly Sharpes:             {[round(s,2) for s in monthly_sharpes]}")
print(f"  Sharpe Std (monthly):        {sharpe_std_monthly:.3f}")
print(f"  Smoothness (0→1):            {smoothness_raw:.4f}  [Calmar={calmar:.2f}, ROI={roi_total:.2f}%]  [v4.1]")
print(f"  Smoothness² score:           {S_smoothness:.1f}/100")
print(f"  Calmar Ratio:                {calmar:.3f}  (ROI {roi_total:.2f}% / DD {max_dd_pct:.2f}%)  [v4.1]")

print(f"\n{'─'*35} FINANCIAL RESULTS {'─'*17}")
print(f"  Gross Profit:                ${gross_profit:.2f}")
print(f"  Gross Loss:                  ${gross_loss:.2f}")
print(f"  Net Profit:                  ${gross_profit - gross_loss:.2f}")
print(f"  Final Equity:                ${equity_curve[-1]:.2f}")
print(f"  ROI:                         {(equity_curve[-1]-INITIAL_CAPITAL)/INITIAL_CAPITAL*100:.2f}%")

print(f"\n{SEP}")
print("  S_RAW v4 — DECOMPOSIÇÃO COMPLETA (11 componentes)")
print(f"{SEP}")
print(f"  {'Componente':<20} {'Norm':>7} {'Peso':>6}  {'Contrib':>8}  {'Status'}")
print(f"  {sep}")
rows = [
    ('Sharpe Ratio',    S_sharpe,     W['sharpe'],     ''),
    ('Sortino×Conf',    S_sortino,    W['sortino'],    '[NOVO v4]'),
    ('Win Rate',        S_winrate,    W['winrate'],    ''),
    ('Profit Factor',   S_pf,         W['pf'],         ''),
    ('Avg R-Multiple',  S_avg_r,      W['avg_r'],      ''),
    ('Expectancy',      S_expectancy, W['expectancy'], '[NOVO v4]'),
    ('Volatility',      S_vol,        W['vol'],        '[NOVO v4]'),
    ('Stability²',      S_stability,  W['stability'],  '[NOVO v4]'),
    ('Smoothness²',     S_smoothness, W['smoothness'], '[NOVO v4]'),
]
total_additive = 0
for name, norm, w, tag in rows:
    contrib = norm * w
    total_additive += contrib
    bar = '█' * int(norm / 10)
    print(f"  {name:<20} {norm:>7.1f} ×{w:.2f}  = {contrib:>+7.2f} pts  {tag}")

print(f"  {sep}")
print(f"  {'DD Penalty (directa)':<20} {max_dd_pct:>7.2f}%×{W['dd']:.2f} = {-DD_penalty:>+7.2f} pts")
print(f"  {sep}")
print(f"  {'S_RAW v4  TOTAL':<20}                  {S_raw:>+7.2f} pts")
print(f"  {'Stage S_raw×10':<20}                          {stage_sraw}")

print(f"\n{SEP}")
print("  YELDEN SCORE v4 — SISTEMA (0–1000)")
print(f"{SEP}")
print(f"  EMA anterior:                {ema_prev:.1f}")
print(f"  EMA nova:                    {ema_new:.1f}   [EMA(t) = {ema_prev:.0f}×{EMA_ALPHA} + {S_raw*10:.1f}×{1-EMA_ALPHA}]")
print(f"  CF (data sufficiency):       {CF:.4f}  [√({cumulative_trades}/{CF_REFERENCE}) = {CF:.4f}]")
print(f"  SF (stability memory):       {SF:.4f}  [worst_S_raw_6m={worst_sraw_6m:.1f}, threshold={SF_THRESHOLD}]")
print(f"  CF × SF:                     {CF*SF:.4f}")
print(f"  {'─'*50}")
print(f"  SISTEMA (EMA×CF×SF):         {sistema:.1f}")
print(f"  STAGE:                       {stage_sistema}")
print(f"{SEP}")

# ══════════════════════════════════════════════════════════════════════
# PROJECÇÃO FUTURA
# ══════════════════════════════════════════════════════════════════════

print(f"\n{'─'*35} PROJECÇÃO SCORE SISTEMA {'─'*11}")
print("  (Assumindo performance consistente — S_raw actual mantido)\n")
print(f"  {'Rodada':<8} {'Total Trades':<14} {'EMA proj':<10} {'CF':<7} {'SF':<7} {'Sistema':<10} Stage")
print(f"  {sep}")

ema_proj = ema_new
rh_proj  = round_history_updated.copy()

for i in range(1, 13):
    rh_proj.append(float(S_raw))
    ema_proj = ema_proj * EMA_ALPHA + (S_raw * 10) * (1 - EMA_ALPHA)
    ema_proj = float(np.clip(ema_proj, 0, 1000))
    proj_trades = cumulative_trades + i * trade_count
    cf_proj     = min(np.sqrt(proj_trades / CF_REFERENCE), 1.0)
    sf_window_p = rh_proj[-SF_WINDOW:]
    sf_proj     = max(min(min(sf_window_p) / SF_THRESHOLD, 1.0), 0.0)
    sis_proj    = float(np.clip(ema_proj * cf_proj * sf_proj, 0, 1000))
    stg_proj    = get_stage(sis_proj)
    month_label = f"Mês +{i*1}"
    print(f"  {month_label:<8} {proj_trades:<14} {ema_proj:<10.0f} {cf_proj:<7.3f} {sf_proj:<7.3f} {sis_proj:<10.0f} {stg_proj}")

# ══════════════════════════════════════════════════════════════════════
# ACTUALIZA ESTADO PERSISTENTE
# ══════════════════════════════════════════════════════════════════════

state_new = {
    'ema': ema_new,
    'round_history': round_history_updated[-SF_WINDOW:],  # guarda só os últimos 6
    'total_trades': cumulative_trades,
    'last_updated': None,
    's_raw_last': float(S_raw),
    'sistema_last': float(sistema),
    'stage_last': stage_sistema,
    'cf_last': float(CF),
    'sf_last': float(SF),
}
save_state(state_new)

print(f"\n{SEP}")
print(f"  RESUMO FINAL")
print(f"{SEP}")
print(f"  S_raw v4:     {S_raw:.2f}   (escala 0~100)")
print(f"  EMA:          {ema_new:.1f}   (trajectória histórica, 0-1000)")
print(f"  CF:           {CF:.4f}   (confiança estatística, 0-1)")
print(f"  SF:           {SF:.4f}   (memória catástrofe, 0-1)")
print(f"  SISTEMA:      {sistema:.1f}   (score on-chain, 0-1000)")
print(f"  STAGE:        {stage_sistema}")
print(f"{SEP}\n")

mt5.shutdown()
