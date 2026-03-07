from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

PK = os.getenv("PRIVATE_KEY")
if not PK.startswith("0x"):
    PK = "0x" + PK

RPC   = "https://polygon-mainnet.g.alchemy.com/v2/4VTK2RA3hYVSgiuPshrx1"
AGENT = "0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc"

w3      = Web3(Web3.HTTPProvider(RPC))
account = w3.eth.account.from_key(PK)
nonce   = w3.eth.get_transaction_count(account.address)

tx = {
    "from":     account.address,
    "to":       AGENT,
    "value":    w3.to_wei(2, "ether"),
    "gas":      21_000,
    "gasPrice": w3.to_wei(150, "gwei"),
    "chainId":  137,
    "nonce":    nonce,
}

signed  = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"Tx: {tx_hash.hex()}")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
print(f"✅ 2 MATIC enviados para o agente")