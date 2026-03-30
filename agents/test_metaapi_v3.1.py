"""
test_metaapi_v3.py — Valida métricas MetaStats vs scorer v4.1
Fix: região correcta + retry + wait_synchronized

py -3.11 test_metaapi_v3.py
"""
import asyncio
import json
from metaapi_cloud_sdk import MetaApi, MetaStats

METAAPI_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJhYTZiMTdjODAyMDU0NTQ1ODdmYTI0Y2M5MDI4NWJlNyIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVzdC1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcnBjLWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6d3M6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJtZXRhc3RhdHMtYXBpIiwibWV0aG9kcyI6WyJtZXRhc3RhdHMtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6InJpc2stbWFuYWdlbWVudC1hcGkiLCJtZXRob2RzIjpbInJpc2stbWFuYWdlbWVudC1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoiY29weWZhY3RvcnktYXBpIiwibWV0aG9kcyI6WyJjb3B5ZmFjdG9yeS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoibXQtbWFuYWdlci1hcGkiLCJtZXRob2RzIjpbIm10LW1hbmFnZXItYXBpOnJlc3Q6ZGVhbGluZzoqOioiLCJtdC1tYW5hZ2VyLWFwaTpyZXN0OnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJiaWxsaW5nLWFwaSIsIm1ldGhvZHMiOlsiYmlsbGluZy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiYWE2YjE3YzgwMjA1NDU0NTg3ZmEyNGNjOTAyODViZTciLCJpYXQiOjE3NzM1MTQ5ODYsImV4cCI6MTc4MTI5MDk4Nn0.Iozw489coBBNadt5wFoXkgw2J_MqqJhjBuTGvdB0IpYZeea5LrohQlZn1gD--RbwbhxC3yOQ8-oi7Je46t67S1VeikX9WEJEUs-9mkWTUZt0mEsu4L_r5ZTdHXTAfFnTzSllIfWtDizEnQvwQAjZdJjhdiNnSnDf91JJU_H9-jef8JmXGbLvDIoffX_WRC7IaItwYSATPJOJeMiEbiUbYkx6AqhNUdsqn_RAiD9kCWACAHC3ryyfPn86MvPBGr80iXGqhdkvLrCZr0XI4kz_5vieZhFSUHSsF7orxdhxzJi5MM-SsOu4wSO7Ir83tv2oqavFzKkO5c24heOQmbf81N0Tl5RIWrJ9pBnC3kBW24uYNzJs7cBDFhi4bA_TVqyiaX01uEaCvkLObNsCBQczbt41UuT9eidtzXV0mv81XT3GIhRVVyMlZbgMI4oieLdFHasoSJwsOXT_gjaITF97Ijp2h3RMfaKn9PNuh-MaY0OKBlY4CTaIicxouOHSTgz0a7IpPeTGr0uNtWa2BHD9MefCoF6Cvclk6Ry0cpsr6OSN5VXVVgnOylNNiCjZFfie6ALZ0ZDDDTNFjZ9A2zim1TjxC2QzQmv3VpK1MiYO7DytoX51n72k2DyoJHE9-9LtH4Ceba1dLBEIY12JfG8I2Mzuyb0pnNEJjaEPU9nW2tw"  # app.metaapi.cloud → API tokens
ACCOUNT_ID    = "b5718259-2806-4bf7-be65-7e019d6e4d06"

async def main():
    api = MetaApi(METAAPI_TOKEN)

    # 1. Busca conta e mostra região
    account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
    print(f"  Nome:   {account.name}")
    print(f"  State:  {account.state}")
    print(f"  Region: {getattr(account, 'region', 'unknown')}")
    print(f"  Server: {account.server}")

    # 2. Deploy se necessário
    if account.state not in ["DEPLOYED", "DEPLOYING"]:
        print("A fazer deploy...")
        await account.deploy()

    # 3. Aguarda ligação ao broker
    print("A aguardar ligação ao broker...")
    await account.wait_connected()
    print("  Ligado!")

    # 4. Aguarda sincronização — crítico para MetaStats funcionar
    print("A aguardar sincronização (20s)...")
    await asyncio.sleep(20)

    # 5. MetaStats — usa domínio genérico (SDK detecta região automaticamente)
    metastats = MetaStats(token=METAAPI_TOKEN)

    print("A calcular métricas...")
    metrics = None
    for attempt in range(4):
        try:
            metrics = await metastats.get_metrics(
                account_id=ACCOUNT_ID,
                include_open_positions=False,
            )
            print("  ✓ Métricas obtidas!")
            break
        except Exception as e:
            print(f"  Tentativa {attempt+1}/4 falhou: {str(e)[:120]}")
            if attempt < 3:
                wait = 20 + attempt * 10
                print(f"  A aguardar {wait}s...")
                await asyncio.sleep(wait)

    if not metrics:
        print("✗ Não foi possível obter métricas. Verifica o URL correcto em:")
        print("  https://app.metaapi.cloud/api-access/api-urls")
        await account.undeploy()
        return

    # 6. Campos críticos para o scorer
    print("\n══ VALIDAÇÃO SCORER v4.1 ══════════════════════════")
    print(f"  Trades total     : {metrics.get('trades')}")
    print(f"  Won / Lost       : {metrics.get('wonTrades')} / {metrics.get('lostTrades')}")
    trades = metrics.get('trades') or 1
    won    = metrics.get('wonTrades') or 0
    win_rate = won / trades * 100
    print(f"  Win Rate         : {win_rate:.1f}%")
    print(f"  Profit Factor    : {metrics.get('profitFactor')}")
    print(f"  Sharpe Ratio     : {metrics.get('sharpeRatio')}")
    print(f"  Sortino Ratio    : {metrics.get('sortinoRatio')}")
    print(f"  Max Drawdown %   : {metrics.get('maxDrawdown')}")
    print(f"  Avg Win          : {metrics.get('averageWin')}")
    print(f"  Avg Loss         : {metrics.get('averageLoss')}")
    print(f"  Profit total     : ${metrics.get('profit')}")
    print(f"  Balance          : ${metrics.get('balance')}")
    print(f"  Gain %           : {metrics.get('gain')}%")

    # 7. Calcula S_raw v4.1
    avg_win  = abs(float(metrics.get('averageWin',  1) or 1))
    avg_loss = abs(float(metrics.get('averageLoss', 1) or 1))
    avg_r    = avg_win / avg_loss if avg_loss > 0 else 0
    wr       = win_rate / 100
    er       = wr * avg_r - (1 - wr)

    sharpe       = min(float(metrics.get('sharpeRatio') or 0) / 2.5, 1.0) * 100 * 0.18
    sort_conf    = min((metrics.get('lostTrades') or 0) / 20, 1.0)
    sortino      = min(float(metrics.get('sortinoRatio') or 0) / 8.0, 1.0) * 100 * 0.08 * sort_conf
    wr_score     = wr * 100 * 0.12
    pf           = float(metrics.get('profitFactor') or 1.0)
    pf_score     = max(0, min((pf - 1.0) / 1.5, 1.0)) * 100 * 0.15
    avgr_score   = min(avg_r / 1.2, 1.0) * 100 * 0.08
    er_score     = min(max(er, 0) / 0.5, 1.0) * 100 * 0.10
    dd           = float(metrics.get('maxDrawdown') or 0)
    dd_penalty   = min(dd, 30) / 30 * 100 * 0.25
    gain         = float(metrics.get('gain') or 0)
    calmar       = (gain / dd) if dd > 0 else 0
    smooth       = (min(calmar / 3.0, 1.0) ** 2) * 100 * 0.12

    s_raw    = max(0, min(sharpe + sortino + wr_score + pf_score + avgr_score + er_score + smooth - dd_penalty, 100))
    cf       = min((trades / 200) ** 0.5, 1.0)
    sistema  = round((300 * 0.85 + s_raw * 10 * 0.15) * cf)
    stage    = "EXPERIMENTAL"
    if   sistema >= 800: stage = "LEGENDARY"
    elif sistema >= 600: stage = "ELITE"
    elif sistema >= 400: stage = "VERIFIED"
    elif sistema >= 200: stage = "PROMISING"

    print(f"\n══ S_RAW v4.1 ══════════════════════════════════════")
    print(f"  Sharpe           : +{sharpe:.1f}")
    print(f"  Sortino×conf     : +{sortino:.1f}  (conf={sort_conf:.2f})")
    print(f"  Win Rate         : +{wr_score:.1f}")
    print(f"  Profit Factor    : +{pf_score:.1f}")
    print(f"  Avg R            : +{avgr_score:.1f}")
    print(f"  Expectancy E(R)  : +{er_score:.1f}  (E(R)={er:.3f})")
    print(f"  Smoothness       : +{smooth:.1f}  (Calmar={calmar:.2f})")
    print(f"  DD Penalty       : -{dd_penalty:.1f}")
    print(f"  ─────────────────────────────────")
    print(f"  S_RAW            : {s_raw:.1f} / 100")
    print(f"  CF               : {cf:.3f}  ({trades} trades)")
    print(f"  SISTEMA          : {sistema} / 1000")
    print(f"  STAGE            : {stage}")

    # 8. Guarda
    with open("metaapi_validation.json", "w") as f:
        json.dump({"metrics": metrics, "s_raw": s_raw, "sistema": sistema, "stage": stage}, f, indent=2, default=str)
    print(f"\n  Raw guardado em metaapi_validation.json")

    # 9. Undeploy
    await account.undeploy()
    print("\n  Undeploy feito. Crédito preservado.")

if __name__ == "__main__":
    asyncio.run(main())
