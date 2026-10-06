# ⚠️ Yelden Protocol — DEPRECATED

> **This repository is no longer maintained.**  
> The current Yelden protocol lives at **[github.com/yeldenfund/yaaf](https://github.com/yeldenfund/yaaf)**.

---

## What happened

Yelden Protocol was originally designed as a DeFi yield distribution system with RWA allocation, a $YLD governance token, tiered UBI, AI agent slashing, and an ERC-4626 vault (yUSD).

**None of these are part of the current protocol.**

After empirical validation of the YAAF scorer, the project pivoted to what actually works: **accountability infrastructure for autonomous trading agents**.

The current Yelden is:
- **YAAF** — a multi-component scoring engine, empirically validated (rho=0.44, p=0.0005 on GMX V2)
- **AIAgentRegistry** — on-chain registry on Polygon with slash and isEligible()
- **No token. No vault. No UBI. No RWA.**

The YLD token, vault, distributor, and ZK verifier are deployed but inactive — historical artifacts on Polygon mainnet. The protocol does not use them.

---

## Where to go

| What you want | Where it is |
|---|---|
| **Current protocol** | [github.com/yeldenfund/yaaf](https://github.com/yeldenfund/yaaf) |
| **Whitepaper v16** | [yaaf/docs/Yelden_Whitepaper_v16.pdf](https://github.com/yeldenfund/yaaf/blob/main/docs/Yelden_Whitepaper_v16.pdf) |
| **Live site** | [yelden.fund](https://yelden.fund) |
| **Contact** | yeldenfund@gmail.com |

---

## What remains in this repo

This repository is kept as a **historical archive** of the v15 design:

- `contracts/YLDToken.sol` — deprecated governance token
- `contracts/YeldenVault.sol` — deprecated ERC-4626 vault
- `contracts/YeldenDistributor.sol` — deprecated yield distributor
- `contracts/ZKVerifier.sol` — deprecated Groth16 verifier
- `contracts/AIAgentRegistry.sol` — superseded by the version in the `yaaf` repo
- `docs/Yelden_Whitepaper_v15.pdf` — superseded by v16
- `circuits/` — ZK contribution circuit (not used)

**Do not build on the deprecated contracts.**

---

## Why the pivot

1. **RWA integration is a 12–18 month effort** requiring legal, regulatory, and custody infrastructure.
2. **A token without product-market fit is a liability.** YLD would have launched into zero demand.
3. **UBI requires yield, yield requires capital, capital requires trust** — which requires the accountability layer first.
4. **The YAAF scorer already has empirical edge** (rho=0.44, p=0.0005). That is a real product.

The current protocol is smaller, focused, and works.

---

_Yelden Protocol — archived October 2026._  
_The current Yelden is at [yeldenfund/yaaf](https://github.com/yeldenfund/yaaf)._
