# Yelden Protocol

> Distribuição de rendimentos RWA · Privacidade ZK · Economia de Agentes de IA · Vault ERC-4626

*Yelden — uma vila medieval inglesa, lar de um castelo do século XII. Um nome que carrega rendimento, história e permanência.*

[🇬🇧 Read in English](./README.md)

[![Testes](https://img.shields.io/badge/testes-198%20aprovados-brightgreen)](./test)
[![Solidity](https://img.shields.io/badge/solidity-0.8.20-blue)](./contracts)
[![Certora](https://img.shields.io/badge/certora-7%2F7%20regras-purple)](./certora)
[![Echidna](https://img.shields.io/badge/echidna-3%2F3%20invariantes-orange)](./echidna)
[![Licença](https://img.shields.io/badge/licença-MIT-green)](./LICENSE)

---

## Visão Geral

Yelden é um protocolo de distribuição de rendimentos construído sobre o padrão ERC-4626. Usuários depositam USDC, recebem cotas yUSD, e o rendimento colhido de Ativos do Mundo Real (RWAs) é automaticamente distribuído por quatro canais: rebase base para depositantes, fundo de regeneração ambiental, reserva para mercados baixistas, e um pool de excedente dividido entre contribuidores humanos (provado via ZK com Groth16) e agentes de IA (validados por Chainlink DON, pontuados por desempenho e economicamente responsáveis).

**O que torna Yelden diferente:** agentes de IA não apenas participam — eles têm "pele no jogo". Agentes fazem stake de $YLD, acumulam uma pontuação de desempenho (0–1000), pagam taxas inversamente proporcionais à sua pontuação e são penalizados por mau comportamento. Pontuação 1000 paga zero. Agentes maliciosos perdem tudo.

---

## Arquitetura

```
                     ┌──────────────────────────────────┐
                     │          Usuário / dApp            │
                     └───────────┬──────────────────────┘
                                 │ deposit(USDC)
                                 ▼
                     ┌──────────────────────────────────┐
                     │         YeldenVault               │
                     │         (ERC-4626)                │
                     │                                   │
                     │  ativo: USDC  cotas: yUSD         │
                     │                                   │
                     │  harvest(rendimentoBruto)         │
                     │  ├─ 4,5% → rebase base (yUSD)    │
                     │  ├─ 5,0% → fundo regen           │
                     │  ├─ excedente × 20% → reserva    │
                     │  └─ excedente × 80% → Distribuidor│
                     └───────────┬──────────────────────┘
                                 │ distribute(excedente)
                                 ▼
                     ┌──────────────────────────────────┐
                     │       YeldenDistributor           │
                     │                                   │
                     │  70% → pool proporcional         │
                     │  20% → pool equalizado           │
                     │  10% → pool bônus ZK             │
                     │    ├─ 95% → contribuidores humanos│
                     │    └─ 5%  → pool de agentes IA   │
                     └──────────┬──────────┬────────────┘
                                │          │
              claimZKBonus()    │          │ releaseAIBonus()
                                ▼          ▼
                     ┌────────────────┐ ┌──────────────────────┐
                     │  ZKVerifier    │ │   AIAgentRegistry    │
                     │  (Groth16)     │ │   (v3 — completo)    │
                     │                │ │                      │
                     │  verifyProof() │ │  pontuação: 0–1000   │
                     │  nullifier     │ │  taxa ∝ (1000−pts)   │
                     │  anti-replay   │ │  slash → queima $YLD │
                     └────────────────┘ └──────────────────────┘
```

---

## Contratos

### `YeldenVault.sol`
Vault compatível com ERC-4626. Aceita USDC, emite cotas yUSD na proporção 1:1 no primeiro depósito. A taxa de câmbio aumenta conforme o rendimento é colhido.

| Função | Descrição |
|---|---|
| `deposit(assets, receiver)` | Deposita USDC, recebe yUSD |
| `withdraw(assets, receiver, owner)` | Queima yUSD, recebe USDC pelo valor do ativo |
| `redeem(shares, receiver, owner)` | Queima yUSD, recebe USDC pelo valor das cotas |
| `harvest(grossYield)` | Dono: distribui o rendimento RWA pelo protocolo |
| `setDistributor(address)` | Dono: conecta o YeldenDistributor |
| `withdrawReserve(to, amount)` | Dono: libera a reserva para mercados baixistas |

**Roteamento de rendimento** (por `harvest`):
```
rendimentoBruto
  ├─ 4,5%  BASE_YIELD_BPS    → rebase no preço do yUSD
  ├─ 5,0%  REGEN_BPS         → fundo ambiental
  └─ 90,5% excedente
       ├─ 20%  YIELD_RESERVE  → reserva para mercados baixistas
       └─ 80%  → YeldenDistributor.distribute()
```

---

### `YeldenDistributor.sol`
Recebe o excedente do vault e aloca para três pools.

| Função | Descrição |
|---|---|
| `distribute(surplus)` | Chamado pelo vault a cada colheita |
| `claimZKBonus(amount, category, proof...)` | Contribuidor humano reivindica do pool ZK |
| `releaseAIBonus(agent, amount)` | Dono libera do pool IA para o agente |
| `setVault(address)` | Dono: autoriza o endereço do vault |
| `setZKVerifier(address)` | Dono: habilita verificação de prova ZK on-chain |
| `poolBalances()` | Visualização: retorna (zkPool, aiPool, totalDistribuído) |

---

### `ZKVerifier.sol` + `contracts/zk/Groth16Verifier.sol`
Verificador de provas Groth16 on-chain. Aceita provas ZK reais geradas pelo circuito `circuits/contribution.circom`.

**Layout das entradas públicas:**
```
input[0] = valid          — 1 se pontuação >= threshold, 0 caso contrário
input[1] = threshold      — pontuação mínima exigida (ex.: 500)
input[2] = nullifierHash  — Poseidon(pontuação, salt, 1) — evita double-claim
input[3] = commitmentHash — Poseidon(pontuação, salt) — prova consistência
```

| Função | Descrição |
|---|---|
| `claimBonus(a, b, c, input[4])` | Verifica prova Groth16, marca nullifier, emite evento |
| `verifyOnly(a, b, c, input[4])` | Visualização: valida prova sem alterar estado |
| `isNullifierUsed(nullifierHash)` | Visualização: verifica se o nullifier já foi usado |

**Garantia de privacidade:** O provador demonstra `pontuação >= threshold` sem revelar a `pontuação` ou o `salt`. Ninguém — incluindo o protocolo — pode vincular uma prova ao seu requerente.

---

### `AIAgentRegistry.sol`
Primitiva de reputação on-chain para agentes de IA autônomos. Formalmente verificado. Qualquer protocolo integra em duas linhas:

```solidity
IAgentRegistry registry = IAgentRegistry(REGISTRY_ADDRESS);
require(registry.isEligible(agent), "Agente nao elegivel");
```

**Modelo de pontuação:** A pontuação começa em 300 na aprovação e cresce apenas por desempenho verificado. Capital não pode comprar uma pontuação maior.

**Modelo de taxas:**
```
taxa mensal = taxaMensal × (1000 − pontuação) / 1000

pontuação 1000 → 0 YLD/mês  (agente perfeito, grátis para sempre)
pontuação 500  → 0,5 YLD/mês
pontuação 0    → 1 YLD/mês  (taxa máxima, auto-eliminação)
```

**Níveis de slash:**

| Nível | Stake Queimado | Status Após |
|---|---|---|
| ADVERTÊNCIA | 10% | ATIVO |
| SUSPENSÃO | 50% | PENDENTE |
| BANIMENTO | 100% | BANIDO permanentemente |

Todas as taxas e $YLD penalizados são queimados para `0x000...dead`. Registro auto-limpante — agentes com baixo desempenho se eliminam sem intervenção de governança.

---

## Circuito ZK

```bash
# Compilar (requer circom 2.x — veja Primeiros Passos)
cd circuits
circom contribution.circom --r1cs --wasm --sym --O2 --output build/

# Verificar prova existente
snarkjs groth16 verify circuits/build/verification_key.json \
  circuits/build/public.json circuits/build/proof.json
```

**Estatísticas do circuito:**
```
instâncias de template:     144
restrições não-lineares:    532
entradas públicas:          3
entradas privadas:          2 (pontuação, salt — nunca revelados)
saídas públicas:            1 (valid)
```

---

## Suite de Testes

```
198 testes aprovados — 0 falhando
```

| Suite | Testes | Descrição |
|---|---|---|
| `YeldenVault.test.js` | 57 | Deploy, depósito, saque, resgate, colheita, reserva |
| `YeldenVault.bearmarket.js` | 8 | Acumulação de reserva, uso, ciclo completo |
| `YeldenVault.concurrency.js` | 5 | 10 usuários simultâneos, operações mistas |
| `YeldenVault.fuzz.js` | 9 | 100 depósitos, 50 saques, 100 colheitas aleatórios |
| `YeldenVault.gas.js` | 10 | Benchmarks de gas, custo da jornada do usuário |
| `YeldenVault.mainnet.js` | 11 | USDC real, oráculos Chainlink, interop Uniswap |
| `reentrancy-test.js` | 1 | Ataque de reentrância bloqueado |
| `AIAgentRegistry.test.js` | 69 | Registro, pontuação, taxas, slash, ciclo de vida |
| `ZKVerifier.test.js` | 16 | Provas Groth16 reais, nullifier, double-claim, manipulação |
| `YeldenDistributor` | 12 | Distribuição de pools, bônus ZK, pool IA |

**Verificação formal:**
```
Certora Prover:   7/7 regras verificadas
Echidna fuzzing:  3/3 invariantes — 10.000 sequências de chamada — zero violações
Mutation testing: 10/10 mortos — 100% mutation score
Cobertura:        95,88% linhas (vault: 100%)
```

**Benchmarks de gas:**
```
depósito (primeiro):    108.179 gas
depósito (segundo):      74.129 gas
saque:                   57.311 gas
colheita:               130.993 gas
registrarAgente:        ~95.000 gas
claimBonus (ZK):       ~280.000 gas  (inclui verificação Groth16 on-chain)
```

---

## Primeiros Passos

### Pré-requisitos
```bash
node >= 18
npm >= 9
rust >= 1.70  # para circom 2.x
```

### Instalação
```bash
git clone https://github.com/yeldenfund/yelden-protocol
cd yelden-protocol
npm install
```

### Executar testes
```bash
# Todos os testes
npx hardhat test

# Verificador ZK (requer artefatos de circuits/build/)
npx hardhat test test/ZKVerifier.test.js

# Registry
npx hardhat test test/AIAgentRegistry.test.js

# Com fork de mainnet
ALCHEMY_KEY=sua_chave npx hardhat test
```

### Compilar circuito ZK (WSL ou Linux)
```bash
# Instalar circom 2.x
git clone https://github.com/iden3/circom.git ~/.circom
cd ~/.circom && cargo build --release
export PATH="$HOME/.circom/target/release:$PATH"

# Compilar
cd /caminho/para/yelden-protocol/circuits
circom contribution.circom --r1cs --wasm --sym --O2 --output build/
```

---

## Estrutura do Projeto

```
yelden-protocol/
├── contracts/
│   ├── YeldenVault.sol           # Vault ERC-4626 — núcleo
│   ├── YeldenDistributor.sol     # Distribuição de rendimentos — 3 pools
│   ├── ZKVerifier.sol            # Verificador de nullifier Groth16
│   ├── AIAgentRegistry.sol       # Reputação de agentes IA — v3
│   └── zk/
│       └── Groth16Verifier.sol   # Gerado pelo snarkjs
├── circuits/
│   ├── contribution.circom       # Circuito ZK — pontuação >= threshold
│   └── build/
│       ├── contribution.r1cs
│       ├── contribution.sym
│       ├── contribution_js/
│       │   └── contribution.wasm
│       ├── contribution_0001.zkey
│       └── verification_key.json
├── test/
│   ├── helpers.js
│   ├── YeldenVault.test.js
│   ├── YeldenVault.bearmarket.js
│   ├── YeldenVault.concurrency.js
│   ├── YeldenVault.fuzz.js
│   ├── YeldenVault.gas.js
│   ├── YeldenVault.mainnet.js
│   ├── reentrancy-test.js
│   ├── AIAgentRegistry.test.js
│   └── ZKVerifier.test.js
├── certora/                      # Especificações de verificação formal
├── echidna/                      # Invariantes de fuzzing
├── hardhat.config.js
└── package.json
```

---

## Roadmap

### v3 — atual
- [x] `AIAgentRegistry.sol` — stake de assinatura, queima de taxas de desempenho, slash
- [x] `ZKVerifier.sol` — verificador Groth16 on-chain real
- [x] `circuits/contribution.circom` — compilado, trusted setup completo, prova verificada
- [x] `contracts/zk/Groth16Verifier.sol` — gerado pelo snarkjs
- [x] 198 testes aprovados

### v4 — próximo
- [ ] Token `$YLD` — ERC-20, 1B de fornecimento fixo, queima, governança
- [ ] `veYLD` — lock com vote-escrow para stake no Registry
- [ ] Adaptadores RWA — Ondo, Centrifuge, Maple
- [ ] Redundância de oráculos — Chainlink primário + Pyth secundário + circuit breaker
- [ ] Integração Chainlink DON — automação real do SCORER_ROLE

---

## Segurança

| Ferramenta | Resultado |
|---|---|
| Certora Prover | 7/7 regras verificadas |
| Echidna | 3/3 invariantes — 10k sequências |
| Mutation testing | 100% score |
| Slither | 40 achados — todos de baixo risco |
| Cobertura | 95,88% linhas |

Um bug real encontrado e documentado: a contabilidade de reserva em `harvest()` pode exceder `totalAssets()` antes de um depósito correspondente. Comportamento esperado confirmado — invariante atualizado nas especificações do Echidna e Certora.

Auditoria comercial (Code4rena ou Trail of Bits) planejada antes do deploy em mainnet.

---

## Como Contribuir

Bounties no DevNet: $500 YLD por bug confirmado, $2.000 por sub-vault aceito.

Veja [CONTRIBUTING.md](./CONTRIBUTING.md) para o guia completo de contribuição.

---

## Licença

MIT
