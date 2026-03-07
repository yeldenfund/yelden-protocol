from web3 import Web3
from dotenv import load_dotenv
import os, json

load_dotenv()

PK = os.getenv("PRIVATE_KEY")
if not PK.startswith("0x"):
    PK = "0x" + PK

RPC = "https://polygon-mainnet.g.alchemy.com/v2/4VTK2RA3hYVSgiuPshrx1"
w3  = Web3(Web3.HTTPProvider(RPC))
account = w3.eth.account.from_key(PK)
print(f"Deployer: {account.address}")
print(f"Balance:  {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} MATIC")

YLD_ADDRESS = os.getenv("YLD_ADDRESS", "0xE5Cc95489eC4Afb957f5C71593f6e4e028410cd4")
VAULT       = account.address  # deployer como vault por agora
MIN_STAKE   = w3.to_wei(50, "ether")
MONTHLY_FEE = w3.to_wei(1, "ether")

with open(r"artifacts\contracts\AIAgentRegistry.sol\AIAgentRegistry.json") as f:
    artifact = json.load(f)

Registry = w3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])

nonce = w3.eth.get_transaction_count(account.address)

BURN_ADDRESS = "0x000000000000000000000000000000000000dEaD"
ADMIN        = account.address

tx = Registry.constructor(
    YLD_ADDRESS,
    MIN_STAKE,
    MONTHLY_FEE,
    VAULT,
    BURN_ADDRESS,
    ADMIN
).build_transaction({
    "from":     account.address,
    "nonce":    nonce,
    "gas":      4_000_000,
    "gasPrice": w3.to_wei(150, "gwei"),
    "chainId":  137,
})

signed  = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"\nTx: {tx_hash.hex()}")
print("Aguardando...")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
print(f"\nAIAgentRegistry: {receipt.contractAddress}")
print(f"https://polygonscan.com/address/{receipt.contractAddress}")
print(f"\nAdiciona no .env:")
print(f"REGISTRY_ADDRESS={receipt.contractAddress}")