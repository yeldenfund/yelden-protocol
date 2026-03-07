from web3 import Web3
from dotenv import load_dotenv
import os, json

load_dotenv()

PK = os.getenv("PRIVATE_KEY")
if not PK.startswith("0x"):
    PK = "0x" + PK

RPC              = "https://polygon-mainnet.g.alchemy.com/v2/4VTK2RA3hYVSgiuPshrx1"
REGISTRY_ADDRESS = "0x32F534265090d8645652b76754B07E6648b51571"
AGENT_ADDRESS    = "0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc"

w3      = Web3(Web3.HTTPProvider(RPC))
account = w3.eth.account.from_key(PK)
print(f"Deployer: {account.address}")

with open(r"artifacts\contracts\AIAgentRegistry.sol\AIAgentRegistry.json") as f:
    artifact = json.load(f)

registry = w3.eth.contract(address=REGISTRY_ADDRESS, abi=artifact["abi"])
nonce    = w3.eth.get_transaction_count(account.address)

tx = registry.functions.approveAgent(AGENT_ADDRESS).build_transaction({
    "from":     account.address,
    "nonce":    nonce,
    "gas":      200_000,
    "gasPrice": w3.to_wei(150, "gwei"),
    "chainId":  137,
})

signed  = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"Tx: {tx_hash.hex()}")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
print(f"✅ Agente aprovado!")
print(f"   https://polygonscan.com/tx/{tx_hash.hex()}")