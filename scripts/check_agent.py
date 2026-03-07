from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider("https://polygon-mainnet.g.alchemy.com/v2/4VTK2RA3hYVSgiuPshrx1"))

with open(r"artifacts\contracts\AIAgentRegistry.sol\AIAgentRegistry.json") as f:
    a = json.load(f)

r     = w3.eth.contract(address="0x32F534265090d8645652b76754B07E6648b51571", abi=a["abi"])
agent = "0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc"

print(f"isActive: {r.functions.isActive(agent).call()}")
print(f"statusOf: {r.functions.statusOf(agent).call()}")
print(f"score:    {r.functions.score(agent).call()}")
print(f"stakeOf:  {r.functions.stakeOf(agent).call()}")
print(f"totalAgents: {r.functions.totalAgents().call()}")
print(f"totalRegistered: {r.functions.totalRegistered().call()}")
info = r.functions.getAgent(agent).call()
print(f"getAgent: {info}")