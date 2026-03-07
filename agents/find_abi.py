import os, json, glob

# Caminhos a procurar
SEARCH_ROOTS = [
    r"C:\Users\Administrator\yelden-protocol",
    r"C:\YeldenBridge",
]

print("=" * 60)
print("PROCURANDO ABI do AIAgentRegistry...")
print("=" * 60)

found = []

for root in SEARCH_ROOTS:
    if not os.path.exists(root):
        print(f"  Pasta não existe: {root}")
        continue
    for dirpath, dirnames, filenames in os.walk(root):
        # Ignorar node_modules e .git
        dirnames[:] = [d for d in dirnames if d not in ('node_modules', '.git', 'cache')]
        for fname in filenames:
            if 'AIAgentRegistry' in fname and fname.endswith('.json'):
                full = os.path.join(dirpath, fname)
                found.append(full)
                print(f"  ✅ Encontrado: {full}")

print()

if not found:
    print("❌ Nenhum ficheiro AIAgentRegistry.json encontrado.")
    print("   Verifica se o projecto está compilado (npx hardhat compile).")
else:
    # Pegar o maior (mais completo)
    best = max(found, key=lambda f: os.path.getsize(f))
    print(f"Usando: {best}")
    print(f"Tamanho: {os.path.getsize(best)} bytes")
    print()

    try:
        with open(best) as f:
            data = json.load(f)

        abi = data.get('abi', [])
        print(f"ABI tem {len(abi)} entradas")
        print()

        # Mostrar funções relevantes
        print("── Funções encontradas ────────────────────────────")
        for item in abi:
            if item.get('type') == 'function':
                inputs = ', '.join(
                    f"{i.get('name','?')}:{i.get('type','?')}"
                    for i in item.get('inputs', [])
                )
                outputs = ', '.join(
                    i.get('type','?')
                    for i in item.get('outputs', [])
                )
                print(f"  {item['name']}({inputs}) → {outputs}")

        print()
        print("── Eventos encontrados ────────────────────────────")
        for item in abi:
            if item.get('type') == 'event':
                inputs = ', '.join(
                    f"{i.get('name','?')}:{i.get('type','?')}"
                    for i in item.get('inputs', [])
                )
                print(f"  event {item['name']}({inputs})")

        # Guardar ABI limpo
        output_path = r"C:\YeldenBridge\registry_abi.json"
        with open(output_path, 'w') as f:
            json.dump(abi, f, indent=2)
        print()
        print(f"✅ ABI guardado em: {output_path}")
        print("   Próximo passo: corre reregister_agent_v2.py")

    except Exception as e:
        print(f"❌ Erro a ler JSON: {e}")

print()
print("=" * 60)
print("FIM")
print("=" * 60)
