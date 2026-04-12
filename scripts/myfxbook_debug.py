"""
myfxbook_debug.py — Debug completo da API Myfxbook
Corre no teu PC local: py -3.11 myfxbook_debug.py
"""
import requests
import json

EMAIL    = "plongen@gmail.com"
PASSWORD = "qA_XYf!:Ki43Jzw"   # preenche aqui

BASE = "https://www.myfxbook.com/api"

# Login com resposta completa
print("=== LOGIN ===")
r = requests.get(f"{BASE}/login.json", params={"email": EMAIL, "password": PASSWORD})
print(f"Status: {r.status_code}")
print(f"Headers: {dict(r.headers)}")
print(f"Body: {r.text}")
print()

data = r.json()
if data.get("error"):
    print(f"ERRO: {data.get('message')}")
    exit()

session = data["session"]
print(f"Session: {session}")
print()

# Testa get-my-accounts com resposta completa
print("=== GET-MY-ACCOUNTS ===")
r2 = requests.get(f"{BASE}/get-my-accounts.json", params={"session": session})
print(f"Status: {r2.status_code}")
print(f"Body: {r2.text[:500]}")
print()

# Tenta também com session na cookie
print("=== GET-MY-ACCOUNTS (com cookie) ===")
s = requests.Session()
s.get(f"{BASE}/login.json", params={"email": EMAIL, "password": PASSWORD})
r3 = s.get(f"{BASE}/get-my-accounts.json", params={"session": session})
print(f"Status: {r3.status_code}")
print(f"Body: {r3.text[:500]}")
