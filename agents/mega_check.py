import json, os, sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

REGISTRY  = "0xca380aC6418f0089CdfE33F1A175F2452A3822d7"
YLD_TOKEN = "0x72D6971A5A13E250fd907E9212A9839D1B24B4b3"  # endereço real do contrato
ABI_PATH  = r"abi\AIAgentRegistry.json"  # gerado pelo fix_all.py

OK   = "OK  "
FAIL = "FAIL"
WARN = "WARN"

results = []

def check(label, status, detail=""):
    icon = {"OK  ": "✅", "FAIL": "❌", "WARN": "⚠️ "}[status]
    line = f"  {icon} [{status}] {label}"
    if detail:
        line += f"\n         → {detail}"
    print(line)
    results.append((status, label, detail))

def section(title):
    print()
    print("─" * 60)
    print(f"  {title}")
    print("─" * 60)

print()
print("=" * 60)
print("  YELDEN MEGA DIAGNÓSTICO")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# ══════════════════════════════════════════════════════════════
# 1. AMBIENTE
# ══════════════════════════════════════════════════════════════
section("1. AMBIENTE — Python e dependências")

check("Python versão", OK, sys.version)

libs = ["web3", "eth_account", "dotenv", "MetaTrader5"]
for lib in libs:
    try:
        __import__(lib.replace("dotenv","dotenv").replace("MetaTrader5","MetaTrader5"))
        check(f"import {lib}", OK)
    except ImportError as e:
        check(f"import {lib}", FAIL, str(e))

# ══════════════════════════════════════════════════════════════
# 2. FICHEIROS LOCAIS
# ══════════════════════════════════════════════════════════════
section("2. FICHEIROS — .env, JSON, ABI")

files = {
    ".env":                    ".env",
    "agent_performance.json":  "agent_performance.json",
    "submission_receipt.json": "submission_receipt.json",
    "mt5_monitor_state.json":  "mt5_monitor_state.json",
    "ABI do contrato":         ABI_PATH,
}
for label, path in files.items():
    if os.path.exists(path):
        size = os.path.getsize(path)
        check(label, OK, f"{path} ({size} bytes)")
    else:
        check(label, FAIL, f"Não encontrado: {path}")

# ══════════════════════════════════════════════════════════════
# 3. VARIÁVEIS DE AMBIENTE
# ══════════════════════════════════════════════════════════════
section("3. VARIÁVEIS DE AMBIENTE — .env")

env_vars = {
    "PRIVATE_KEY":     ("obrigatório", lambda v: len(v) >= 64),
    "RPC_URL":         ("obrigatório", lambda v: v.startswith("http")),
    "AGENT_ADDRESS":   ("obrigatório", lambda v: v.startswith("0x") and len(v) == 42),
    "ETH_RPC_URL":     ("alternativo", lambda v: v.startswith("http")),
    "TELEGRAM_TOKEN":  ("opcional",    lambda v: len(v) > 10),
    "TELEGRAM_CHAT_ID":("opcional",    lambda v: len(v) > 3),
    "YLD_TOKEN_ADDRESS":("opcional",   lambda v: v.startswith("0x")),
}

env_ok = {}
for var, (kind, validator) in env_vars.items():
    val = os.getenv(var)
    if val is None:
        status = FAIL if kind == "obrigatório" else WARN
        check(f"{var} ({kind})", status, "Não definido")
        env_ok[var] = False
    else:
        try:
            valid = validator(val)
            if valid:
                masked = val[:6] + "..." + val[-4:] if len(val) > 10 else val
                check(f"{var} ({kind})", OK, masked)
                env_ok[var] = True
            else:
                check(f"{var} ({kind})", WARN, f"Valor suspeito: {val[:20]}...")
                env_ok[var] = False
        except:
            check(f"{var} ({kind})", WARN, "Erro ao validar")
            env_ok[var] = False

# ══════════════════════════════════════════════════════════════
# 4. CONECTIVIDADE WEB3
# ══════════════════════════════════════════════════════════════
section("4. CONECTIVIDADE — Web3 e Ethereum")

w3 = None
account = None

try:
    from web3 import Web3
    from eth_account import Account

    rpc = os.getenv("RPC_URL") or os.getenv("ETH_RPC_URL")
    w3  = Web3(Web3.HTTPProvider(rpc))

    if w3.is_connected():
        check("Conexão RPC", OK, rpc[:50])
    else:
        check("Conexão RPC", FAIL, f"Sem resposta: {rpc}")
        w3 = None
except Exception as e:
    check("Conexão RPC", FAIL, str(e))

if w3:
    try:
        chain = w3.eth.chain_id
        expected = 11155111  # Sepolia
        if chain == expected:
            check("Chain ID", OK, f"{chain} (Sepolia ✓)")
        else:
            check("Chain ID", WARN, f"{chain} — esperado {expected} (Sepolia)")
    except Exception as e:
        check("Chain ID", FAIL, str(e))

    try:
        pk = os.getenv("PRIVATE_KEY")
        account = Account.from_key(pk)
        check("Private Key → Wallet", OK, account.address)
    except Exception as e:
        check("Private Key → Wallet", FAIL, str(e))
        account = None

    if account:
        try:
            bal = w3.from_wei(w3.eth.get_balance(account.address), 'ether')
            status = OK if bal > 0.001 else WARN
            check("ETH Balance", status, f"{bal:.6f} ETH")
        except Exception as e:
            check("ETH Balance", FAIL, str(e))

        try:
            nonce = w3.eth.get_transaction_count(account.address)
            check("Nonce actual", OK, str(nonce))
        except Exception as e:
            check("Nonce", FAIL, str(e))

# ══════════════════════════════════════════════════════════════
# 5. ABI E CONTRATO
# ══════════════════════════════════════════════════════════════
section("5. CONTRATO — ABI e estado on-chain")

abi = None
registry = None

try:
    with open(ABI_PATH) as f:
        abi = json.load(f)['abi']
    fn_names = [i['name'] for i in abi if i.get('type') == 'function']
    check("ABI carregado", OK, f"{len(abi)} entradas, {len(fn_names)} funções")

    required_fns = ["updateScore", "registerAgent", "isActive", "score", "minStake"]
    for fn in required_fns:
        if fn in fn_names:
            check(f"  função {fn}()", OK)
        else:
            check(f"  função {fn}()", FAIL, "Não existe no ABI — contrato diferente?")

except Exception as e:
    check("ABI carregado", FAIL, str(e))

if w3 and abi:
    try:
        code = w3.eth.get_code(w3.to_checksum_address(REGISTRY))
        if len(code) > 10:
            check("Contrato deployado", OK, f"{len(code)} bytes em {REGISTRY}")
        else:
            check("Contrato deployado", FAIL, "Sem bytecode — endereço errado?")
    except Exception as e:
        check("Contrato deployado", FAIL, str(e))

    try:
        registry = w3.eth.contract(
            address=w3.to_checksum_address(REGISTRY), abi=abi)
    except Exception as e:
        check("Instância do contrato", FAIL, str(e))

# ══════════════════════════════════════════════════════════════
# 6. ESTADO DO AGENT
# ══════════════════════════════════════════════════════════════
section("6. AGENT — Estado no registry")

agent_registered = False

if registry and account:
    agent_addr = os.getenv("AGENT_ADDRESS", account.address)

    for fn_name, label in [
        ("isActive",   "isActive"),
        ("isEligible", "isEligible"),
        ("score",      "score on-chain"),
        ("stakeOf",    "stake"),
        ("statusOf",   "statusOf"),
    ]:
        try:
            result = getattr(registry.functions, fn_name)(
                w3.to_checksum_address(agent_addr)).call()
            if fn_name == "stakeOf":
                result = f"{w3.from_wei(result, 'ether')} YLD"
            if fn_name == "isActive":
                agent_registered = bool(result)
                status = OK if result else FAIL
            else:
                status = OK
            check(label, status, str(result))
        except Exception as e:
            check(label, FAIL, str(e))

    try:
        min_stake = registry.functions.minStake().call()
        check("minStake", OK, f"{w3.from_wei(min_stake, 'ether')} YLD")
    except Exception as e:
        check("minStake", FAIL, str(e))

    # SCORER_ROLE
    try:
        role = registry.functions.SCORER_ROLE().call()
        has  = registry.functions.hasRole(role, w3.to_checksum_address(agent_addr)).call()
        check("SCORER_ROLE", OK if has else WARN,
              f"Wallet {'TEM' if has else 'NÃO TEM'} SCORER_ROLE")
    except Exception as e:
        check("SCORER_ROLE", WARN, str(e))

# ══════════════════════════════════════════════════════════════
# 7. YLD TOKEN
# ══════════════════════════════════════════════════════════════
section("7. YLD TOKEN — Balance e allowance")

if w3 and account:
    ERC20_ABI = [
        {"inputs":[{"type":"address"}],"name":"balanceOf","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
        {"inputs":[{"type":"address"},{"type":"address"}],"name":"allowance","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    ]
    try:
        yld = w3.eth.contract(address=w3.to_checksum_address(YLD_TOKEN), abi=ERC20_ABI)
        bal = yld.functions.balanceOf(account.address).call()
        alw = yld.functions.allowance(account.address, w3.to_checksum_address(REGISTRY)).call()
        check("YLD balance",   OK if bal > 0 else FAIL, f"{w3.from_wei(bal,'ether')} YLD")
        check("YLD allowance", OK if alw > 0 else WARN, f"{w3.from_wei(alw,'ether')} YLD aprovado para Registry")
    except Exception as e:
        check("YLD Token", FAIL, str(e))

# ══════════════════════════════════════════════════════════════
# 8. FICHEIROS DE DADOS
# ══════════════════════════════════════════════════════════════
section("8. DADOS — agent_performance.json")

try:
    with open("agent_performance.json") as f:
        perf = json.load(f)

    score_val = perf.get("accumulated_score") or perf.get("consistency_score")
    trades    = perf.get("total_trades", 0)
    win_rate  = perf.get("win_rate", 0)
    sharpe    = perf.get("sharpe_ratio", 0)

    check("score",      OK if score_val else FAIL, str(score_val))
    check("total_trades", OK if trades > 0 else WARN, str(trades))
    check("win_rate",   OK, f"{win_rate}%")
    check("sharpe",     OK, str(sharpe))

    # Verificar campos esperados pelo reporter
    for field in ["accumulated_score", "consistency_score", "total_trades", "window_start"]:
        if field in perf:
            check(f"  campo '{field}'", OK)
        else:
            check(f"  campo '{field}'", WARN, "Ausente — reporter pode falhar")

except FileNotFoundError:
    check("agent_performance.json", FAIL, "Ficheiro não existe — corre mt5_monitor.py primeiro")
except Exception as e:
    check("agent_performance.json", FAIL, str(e))

# ══════════════════════════════════════════════════════════════
# 9. TELEGRAM
# ══════════════════════════════════════════════════════════════
section("9. TELEGRAM — Conectividade")

try:
    import urllib.request, ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    token   = os.getenv("TELEGRAM_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/getMe"
        req = urllib.request.urlopen(url, timeout=5)
        data = json.loads(req.read())
        if data.get("ok"):
            check("Telegram API", OK, f"Bot: @{data['result']['username']}")
        else:
            check("Telegram API", FAIL, str(data))
    else:
        check("Telegram API", WARN, "TOKEN ou CHAT_ID não configurado")
except Exception as e:
    check("Telegram API", FAIL, f"Timeout ou bloqueado: {e}")

# ══════════════════════════════════════════════════════════════
# 10. RESUMO E PLANO DE ACÇÃO
# ══════════════════════════════════════════════════════════════
section("10. RESUMO")

total_ok   = sum(1 for r in results if r[0] == OK)
total_warn = sum(1 for r in results if r[0] == WARN)
total_fail = sum(1 for r in results if r[0] == FAIL)

print(f"  ✅ OK  : {total_ok}")
print(f"  ⚠️  WARN: {total_warn}")
print(f"  ❌ FAIL: {total_fail}")

failures = [r for r in results if r[0] == FAIL]
if failures:
    print()
    print("  FALHAS A CORRIGIR:")
    for _, label, detail in failures:
        print(f"    ❌ {label}")
        if detail:
            print(f"       {detail}")

print()
if not agent_registered:
    print("  PRÓXIMO PASSO: Agent não está registado.")
    print("  Corre: python fix_registry.py")
elif total_fail == 0:
    print("  Pipeline está operacional.")
    print("  Corre: python yelden_reporter.py")
else:
    print("  Corrige as FALHAS acima antes de continuar.")

print()
input("Prima ENTER para sair...")
