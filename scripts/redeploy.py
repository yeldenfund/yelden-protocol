from web3 import Web3
from dotenv import load_dotenv
import os, json

load_dotenv()

PK = os.getenv("PRIVATE_KEY")
if not PK.startswith("0x"):
    PK = "0x" + PK

w3 = Web3(Web3.HTTPProvider("https://polygon-mainnet.g.alchemy.com/v2/4VTK2RA3hYVSgiuPshrx1"))
account = w3.eth.account.from_key(PK)
print(f"Deployer: {account.address}")

with open(r"artifacts\contracts\YLDToken.sol\YLDToken.json") as f:
    artifact = json.load(f)

YLDToken = w3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])
supply   = w3.to_wei(1_000_000, "ether")

tx = YLDToken.constructor(
    "Yelden Token", "YLD", supply, account.address
).build_transaction({
    "from":     account.address,
    "nonce":    0,
    "gas":      3_000_000,
    "gasPrice": w3.to_wei(150, "gwei"),
    "chainId":  137,
})

signed  = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"Tx: {tx_hash.hex()}")
print("Aguardando...")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
print(f"YLDToken: {receipt.contractAddress}")
print(f"https://polygonscan.com/address/{receipt.contractAddress}")