# Yelden Protocol

> Decentralized Yield Distribution · AI Agent Economy · Tiered UBI · ERC-4626

*Yelden — a medieval English village, home to a 12th century castle. A name that carries yield, history, and permanence.*

[![Tests](https://img.shields.io/badge/tests-209%20passing-brightgreen)](./test)
[![Solidity](https://img.shields.io/badge/solidity-0.8.20-blue)](./contracts)
[![Certora](https://img.shields.io/badge/certora-7%2F7%20rules-purple)](./certora)
[![Echidna](https://img.shields.io/badge/echidna-3%2F3%20invariants-orange)](./echidna)
[![Mainnet](https://img.shields.io/badge/polygon-mainnet-8247e5)](https://polygonscan.com)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

---

## The Problem

Three structural failures define the current DeFi landscape:

**1. Yield Without Merit** — current protocols distribute returns based on capital size alone. A whale who deposits $10M earns proportionally more than a contributor who builds infrastructure or creates real economic value. Capital dominance displaces merit.

**2. UBI Without Accountability** — flat distributions create moral hazard. Without feedback loops, UBI degenerates into subsidy.

**3. AI Agents Without Skin in the Game** — autonomous trading agents operate with no accountability layer. If they underperform, they simply stop or restart under a new address. No financial consequence for failure. No credible track record.

*"An agent that cannot lose cannot be trusted. A system that cannot penalize failure cannot allocate capital rationally."* — Taleb, Skin in the Game

**The 24% Loophole:** an agent reaches 24% drawdown, stops trading, avoids the 25% slash threshold. Stake preserved. Vault absorbs the loss. YAAF closes this with a dual-trigger slash.

**The Liquidity Singularity:** when hundreds of AI agents share training data, they converge into simultaneous positions — creating systemic liquidity collapse. Nobody in DeFi is measuring this. YAAF v1.3 introduces the first on-chain Systemic Correlation Index (SCI) to detect and prevent it.

---

## What Yelden Solves

| Problem | Solution |
|---|---|
| Yield without merit | YAAF Score gates fee rates and allocation. Higher score → lower cost → larger share. |
| UBI without accountability | Human contributors earn from equalized pool only when ZK proofs confirm real participation. |
| AI agents without consequence | Agents stake YLD, pay fees inversely proportional to score, slashed for underperformance. |
| No track record | Sistema score compounds over time via EMA. Cannot be faked. |
| No independent verification | Multi-scorer consensus — analogous to rating agencies for AI agents. |

---

## Architecture

```
                     ┌──────────────────────────────────┐
                     │          User / dApp              │
                     └───────────┬──────────────────────┘
                                 │ deposit(USDC)
                                 ▼
                     ┌──────────────────────────────────┐
                     │         YeldenVault               │
                     │         (ERC-4626 · yUSD)         │
                     │                                   │
                     │  harvest(grossYield)              │
                     │  ├─ 4.5% → base rebase (yUSD)    │
                     │  ├─ 5.0% → regen fund            │
                     │  ├─ surplus × 20% → yieldReserve │
                     │  └─ surplus × 80% → Distributor  │
                     └───────────┬──────────────────────┘
                                 │ distribute(surplus)
                                 ▼
                     ┌──────────────────────────────────┐
                     │       YeldenDistributor           │
                     │                                   │
                     │  70% → proportional pool         │
                     │  20% → equalized pool (UBI)      │
                     │  10% → ZK bonus pool             │
                     │    ├─ 50% → human contributors   │
                     │    ├─ 30% → AI agent rewards     │
                     │    └─ 20% → scorer pool          │
                     └──────────┬──────────┬────────────┘
                                │          │
              claimZKBonus()    │          │ releaseAIBonus()
                                ▼          ▼
                     ┌────────────────┐ ┌──────────────────────┐
                     │  ZKVerifier    │ │   AIAgentRegistry    │
                     │  (Groth16)     │ │   (YAAF v1.3)        │
                     │                │ │                      │
                     │  verifyProof() │ │  SISTEMA: 0–1000     │
                     │  nullifier     │ │  Kelly allocation    │
                     │  anti-replay   │ │  DSR anti-overfit    │
                     └────────────────┘ │  slash → UBI        │
                                        └──────────────────────┘
```

---

## YAAF v1.3 — Yelden Agent Accountability Framework

YAAF derives every number from the agent's actual trading record. No fixed stake. No arbitrary allocation. No gameable threshold.

### Mathematical Foundations

| Component | Formula | Literature |
|---|---|---|
| Kelly Criterion | `f* = W - (1-W)/R` | Kelly, 1956 |
| Adaptive Kelly | `f_YAAF = f* × Kelly_scale(n)` | MacLean et al., 2011 |
| Cramér-Lundberg | `ψ(u) = exp(-2μu/σ²)` | Cramér, 1930 |
| Deflated Sharpe (DSR) | `DSR = Φ(SR / σ_SR₀)` | Bailey & López de Prado, 2014 |
| CVaR | `E[Loss \| Loss > VaR_α]` | Rockafellar & Uryasev, 2000 |
| Correlation Penalty | `S_final = S_RAW × D_factor(ρ)` | Markowitz, 1952 |
| Systemic Slash | `δ_slash(t) = 0.25 + 0.15 × SCI(t)` | Adrian & Brunnermeier, 2016 |

### S_RAW v4.1 — 11 Components

```
S_RAW = (Sharpe×DSR   × 0.18   ← DSR gate: penalises statistical noise
       + Sortino×CF   × 0.08   ← downside risk, confidence-weighted
       + Win Rate     × 0.12
       + Profit Fac   × 0.15
       + Avg R        × 0.08   ← scale-free R-multiple
       + Expectancy   × 0.10   ← E(R) = WR×AvgR - (1-WR)
       + Volatility   × 0.07
       + Stability²   × 0.12   ← monthly Sharpe consistency, squared
       + Smoothness²  × 0.12)  ← Calmar², rewards smooth equity curves
       - MaxDD%       × 0.25   ← direct penalty, no ceiling
```

### SISTEMA Score (0–1000)

```
SISTEMA = EMA × CF × SF

EMA(t)  = EMA(t-1) × 0.85 + S_RAW×10 × 0.15   (memory: 85% history, initial: 300)
CF      = min(sqrt(trades / 200), 1.0)           (confidence factor, full at 200 trades)
SF      = min(worst_S_RAW_6_batches / 40, 1.0)  (safety factor, penalises inconsistency)
```

### Stage Classification & Capital Allocation

| Stage | SISTEMA | Capital Multiplier | Min Stake | Max Slash |
|---|---|---|---|---|
| EXPERIMENTAL | 0–199 | 0.5× | 50 YLD | 100% |
| PROMISING | 200–399 | 2.0× | 200 YLD | 100% |
| VERIFIED | 400–599 | 5.0× | 500 YLD | 75% |
| ELITE | 600–799 | 10.0× | 1,000 YLD | 50% |
| LEGENDARY | 800–1000 | 20.0× | 2,000 YLD | 50% |

```
C_allocated = min(C_kelly, C_stage)
C_kelly     = f* × Kelly_scale(n) × CF × V_vault
```

### Dual-Trigger Slash (closes the 24% loophole)

```
Slash = max(Slash_DD(δ), Slash_CapLoss(loss / C_alloc))

Slash_DD:      0 if δ<10%    | 0.4×(δ-0.10)×S if 10-25% | β×S if δ≥25%
Slash_CapLoss: 0 if loss<10% | 0.4×(loss%-0.10)×S        | β×S if loss≥20%
```

**Slash distribution:** 50% burned · 30% to vault depositors · **20% to UBI pool (verified humans)**

### DSR — Anti-Overfitting Gate

```
σ_SR₀ = sqrt((1 - skew×SR + (kurt-1)/4×SR²) / (T-1))
DSR   = Φ(SR / σ_SR₀)
```

Agents with DSR < 95% have their Sharpe contribution penalised. High kurtosis makes the gate more conservative — not less.

### YAAF v1.3 — Systemic Risk Extensions

**Correlation-Adjusted Score** (prevents Liquidity Singularity):
```
S_final     = S_RAW × D_factor(ρ)
D_factor(ρ) = 1 - 0.80 × max(0, ρ - 0.50)
```

**Asynchronous Slash** (prevents cascade):
```
δ_slash(t) = 0.25 + 0.15 × SCI(t)
SCI(t)     = capital-weighted avg pairwise correlation across pool
```

---

## Empirical Validation — Markowitz Bot (ERC-8004 #27703)

All YAAF parameters calibrated to production data from the first registered agent on Polygon Mainnet.

| Metric | Value | Significance |
|---|---|---|
| Live trades | 122 | Real MT5 executions |
| Win rate | 58.68% | Positive edge confirmed |
| Sharpe (normal period) | 1.44 | Above average |
| DSR | 99.999% | Skill confirmed, not noise |
| Max drawdown | 3.47–6.81% | Well inside 25% threshold |
| Kurtosis | 12.13 | Fat tails — bootstrap MC required |
| Ruin rate | 0.0% (5,000 bootstrap paths) | Kelly absorbs fat tails |
| SISTEMA | 220 PROMISING | Honest — stress period reflected |

Bootstrap Monte Carlo samples directly from real trades preserving the actual fat-tail distribution. 0.0% ruin rate confirmed — Kelly-constrained sizing (2.82% per trade) absorbs individual fat-tail events at the portfolio level.

---

## Deployed Contracts — Polygon Mainnet

| Contract | Address | Standard |
|---|---|---|
| YLD Token | `0xE304cafC87698b0056a84f993B7Ed976116eD711` | ERC-20 |
| YeldenVault (yUSD) | `0x636c04e1C0564678447560766201fB784A79c930` | ERC-4626 |
| YeldenDistributor | `0x56a0F3A0a18F3Ed658e0249D0EBc75CF61BA0629` | Custom |
| ZKVerifier | `0x7aDCAf3A1046f5204dc2334fEd742d592cf6fdB5` | Groth16 |
| AIAgentRegistry | `0xbC102cDec0DD007E7739ac213b62d5B031B22aF1` | Custom |
| Markowitz Bot | `0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc` | ERC-8004 |

---

## YLD Token

- **Fixed supply:** 1,000,000,000 YLD — no further minting, enforced at EVM level
- **Deflationary:** agent fees burned · slash burned · carbon offset burns · transaction fee buyback-burn
- **Governance:** veYLD (vote-escrowed) — lock duration up to 4 years · non-transferable · decays linearly

**Fee model (agents):**
```
monthly fee = 1 YLD × (1000 − score) / 1000

score 1000 → 0 YLD/month   (excellence is free)
score 500  → 0.5 YLD/month
score 0    → 1 YLD/month   (self-eliminates)
```

---

## What's Live Today

| Layer | Status |
|---|---|
| 5 contracts deployed — Polygon mainnet | ✅ Live |
| 209 tests · Certora 7/7 · Echidna 3/3 | ✅ Live |
| ZK circuit — Groth16, contribution.circom | ✅ Live |
| YAAF v1.3 scoring oracle (DSR, Kelly, CVaR, Volume Axiom) | ✅ Live |
| `join.yelden.fund` — any MT5 agent → full YAAF score + diagnosis + leaderboard | ✅ Live |
| First agent active: 122 trades, score on-chain | ✅ Live |
| Wyoming DAO LLC — Operating Agreement v4 | 🔜 Filing in progress |
| Chainlink DON — decentralised scoring consensus | 🔜 Q2 2026 |
| Chainlink Automation — automatic slash execution | 🔜 Q2 2026 |
| Genesis Scorer Program (3–5 independent scorers) | 🔜 Q2 2026 |
| veYLD governance contract | 🔜 Q3 2026 |
| Vault with real RWA capital | 🔜 Q3 2026 |
| Formal audit (Code4rena / Sherlock) | 🔜 Phase 2 |

---

## Contracts

### `YeldenVault.sol` — ERC-4626

```
deposit(assets, receiver)        → mint yUSD shares
withdraw(assets, receiver, owner) → burn yUSD, return USDC
harvest(grossYield)              → distribute RWA yield across protocol
```

**Yield routing:**
```
grossYield
  ├─ 4.5%  → rebased into yUSD price (depositor yield)
  ├─ 5.0%  → regen fund
  └─ 90.5% surplus
       ├─ 20% → bear market reserve
       └─ 80% → YeldenDistributor
```

### `AIAgentRegistry.sol` — YAAF enforcement

Any protocol integrates in two lines:
```solidity
IAgentRegistry registry = IAgentRegistry(0xbC102cDec0DD007E7739ac213b62d5B031B22aF1);
require(registry.isEligible(agent), "Agent not eligible");
```

**Slash levels:**

| Level | Stake Burned | Status |
|---|---|---|
| WARNING | 10% | ACTIVE |
| SUSPENSION | 50% | PENDING |
| BAN | 100% | BANNED |

### `ZKVerifier.sol` — Groth16 on-chain

```
input[0] = valid          — 1 if score >= threshold
input[1] = threshold      — minimum score required
input[2] = nullifierHash  — Poseidon(score, salt, 1) — prevents double-claim
input[3] = commitmentHash — Poseidon(score, salt)
```

**Privacy guarantee:** prover demonstrates `score >= threshold` without revealing `score` or `salt`.

---

## ZK Circuit

```bash
cd circuits
circom contribution.circom --r1cs --wasm --sym --O2 --output build/
snarkjs groth16 verify circuits/build/verification_key.json \
  circuits/build/public.json circuits/build/proof.json
```

**Stats:** 144 template instances · 532 non-linear constraints · 2 private inputs (score, salt — never revealed)

---

## Test Suite

```
209 tests passing — 0 failing
```

| Suite | Tests |
|---|---|
| YeldenVault (deployment, deposit, withdraw, harvest) | 57 |
| YeldenVault (bear market reserve) | 8 |
| YeldenVault (10 concurrent users) | 5 |
| YeldenVault (100 random deposits, 100 harvests) | 9 |
| YeldenVault (gas benchmarks) | 10 |
| YeldenVault (mainnet fork — real USDC, Chainlink) | 11 |
| AIAgentRegistry (registration, scoring, slashing) | 69 |
| ZKVerifier (real Groth16 proofs, nullifier, double-claim) | 16 |
| YeldenDistributor | 12 |
| Reentrancy attack | 1 |
| YAAF scorer integration | 11 |

**Formal verification:**
```
Certora Prover:   7/7 rules verified
Echidna fuzzing:  3/3 invariants — 10,000 call sequences — zero violations
Mutation testing: 10/10 killed — 100% mutation score
Coverage:         95.88% lines (vault: 100%)
```

**Gas benchmarks:**
```
deposit (first):     108,179 gas
deposit (second):     74,129 gas
harvest:             130,993 gas
registerAgent:       ~95,000 gas
claimBonus (ZK):    ~280,000 gas
```

---

## Getting Started

```bash
git clone https://github.com/yeldenfund/yelden-protocol
cd yelden-protocol
npm install
npx hardhat test
```

**Run scoring oracle locally:**
```bash
cd agents
pip install flask flask-limiter flask-cors metaapi-cloud-sdk httpx python-dotenv
python yelden_scorer_api.py
# POST http://localhost:8080/join — any MT5 credentials → full YAAF v1.3 score
```

**Compile ZK circuit (WSL or Linux):**
```bash
git clone https://github.com/iden3/circom.git && cd circom
cargo build --release
cd /path/to/yelden-protocol/circuits
circom contribution.circom --r1cs --wasm --sym --O2 --output build/
```

---

## Security

| Tool | Result |
|---|---|
| Certora Prover | 7/7 rules verified |
| Echidna | 3/3 invariants — 10k sequences — zero violations |
| Mutation testing | 100% score |
| Slither | 40 findings — all low risk |
| Coverage | 95.88% lines |
| Emergency pause | 3-of-5 security multisig |

Commercial audit (Code4rena or Trail of Bits) planned before vault goes live with real capital.

---

## Governance

| Parameter | Value |
|---|---|
| Min proposal threshold | 1,000 veYLD |
| Voting period | 3–14 days |
| Quorum | 10% of outstanding veYLD |
| Standard approval | > 50% |
| Supermajority | ≥ 67% (token supply changes, slash %, treasury > 10%) |
| Contract upgrades | 48-hour timelock + supermajority |

---

## Legal Structure

Yelden Protocol is structured as a Wyoming DAO LLC (W.S. § 17-31-101 et seq.). Operating Agreement v4 drafted — formal incorporation in progress.

---

## Technical Co-founder

Yelden is seeking a technical co-founder to own:

- **Chainlink DON** — decentralised YAAF scoring consensus (replace centralised oracle)
- **Chainlink Automation** — automatic slash execution on DD/capital loss triggers
- **YeldenVault.sol with real capital** — ERC-4626 vault allocating by SISTEMA score
- **Long-term protocol design** — Phase 2 and beyond

Production Solidity + DeFi primitives at contract level required.

Contact: **yeldenfund@gmail.com**

---

## Project Structure

```
yelden-protocol/
├── contracts/
│   ├── YeldenVault.sol           # ERC-4626 vault
│   ├── YeldenDistributor.sol     # Yield distribution engine
│   ├── ZKVerifier.sol            # Groth16 nullifier verifier
│   ├── AIAgentRegistry.sol       # AI agent registry + YAAF enforcement
│   └── zk/Groth16Verifier.sol    # Generated by snarkjs
├── circuits/
│   ├── contribution.circom       # ZK circuit — score >= threshold
│   └── build/
├── agents/
│   ├── yelden_scorer_api.py      # YAAF v1.3 scoring engine (Flask)
│   └── leaderboard.json          # Persistent agent leaderboard
├── test/
├── certora/
├── echidna/
├── docs/
│   ├── YAAF_v1.3_whitepaper.pdf
│   └── Yelden_Whitepaper_v15.pdf
└── www/
    └── join.html                 # Agent onboarding portal
```

---

## Resources

- Website: [yelden.fund](https://yelden.fund)
- Agent scoring: [join.yelden.fund](https://join.yelden.fund)
- Live dashboard: [yelden.fund/agent](https://yelden.fund/agent)
- Whitepaper v15: [`/docs`](./docs)
- Contact: yeldenfund@gmail.com · [@yeldenfund](https://twitter.com/yeldenfund)

---

## References

Bailey, D.H. & López de Prado, M. (2014). The Deflated Sharpe Ratio. *Journal of Portfolio Management*, 40(5).

Kelly, J.L. (1956). A New Interpretation of Information Rate. *Bell System Technical Journal*, 35.

Cramér, H. (1930). On the Mathematical Theory of Risk. Skandia Jubilee Volume.

Rockafellar, R.T. & Uryasev, S. (2000). Optimization of Conditional Value-at-Risk. *Journal of Risk*, 2(3).

MacLean, Thorp & Ziemba (2011). The Kelly Capital Growth Investment Criterion. World Scientific.

Markowitz, H. (1952). Portfolio Selection. *Journal of Finance*, 7(1).

Adrian, T. & Brunnermeier, M.K. (2016). CoVaR. *American Economic Review*, 106(7).

López de Prado, M. (2018). Advances in Financial Machine Learning. Wiley.

Taleb, N.N. (2018). Skin in the Game. Random House.

---

*Yelden Protocol DAO LLC — yelden.fund · Polygon Mainnet · v15 Final · March 2026*
