from web3 import Web3
from dotenv import load_dotenv
import os, json

load_dotenv()

RPC = "https://polygon-mainnet.g.alchemy.com/v2/4VTK2RA3hYVSgiuPshrx1"
PK  = os.getenv("PRIVATE_KEY")
if not PK.startswith("0x"):
    PK = "0x" + PK

w3 = Web3(Web3.HTTPProvider(RPC))
account = w3.eth.account.from_key(PK)
print(f"Deployer: {account.address}")
print(f"Balance:  {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} MATIC")

# ABI + Bytecode do YLDToken — compilado pelo Hardhat
artifact_path = r"artifacts\contracts\YLDToken.sol\YLDToken.json"
with open(artifact_path) as f:
    artifact = json.load(f)

abi      = artifact["abi"]
bytecode = artifact["bytecode"]

YLDToken = w3.eth.contract(abi=abi, bytecode=bytecode)

nonce    = w3.eth.get_transaction_count(account.address)
supply   = w3.to_wei(1_000_000, "ether")

tx = YLDToken.constructor(
    "Yelden Token", "YLD", supply, account.address
).build_transaction({
    "from":     account.address,
    "nonce":    nonce,
    "gas":      3_000_000,
    "gasPrice": w3.to_wei(50, "gwei"),
    "chainId":  137,
})

signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"\nTx enviada: {tx_hash.hex()}")
print("Aguardando confirmação...")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
print(f"YLDToken deployado: {receipt.contractAddress}")
print(f"https://polygonscan.com/address/{receipt.contractAddress}")