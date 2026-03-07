@echo off
echo ============================================
echo  Yelden Protocol - Agent Bridge
echo ============================================
echo.

cd C:\YeldenBridge
python -c "
from web3 import Web3
import os
from dotenv import load_dotenv
load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv('RPC_URL')))
# Pegar o bytecode do contrato
code = w3.eth.get_code('0xca380aC6418f0089CdfE33F1A175F2452A3822d7')
print('Bytecode size:', len(code), 'bytes')
"