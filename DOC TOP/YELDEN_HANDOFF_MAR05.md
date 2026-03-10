# Yelden Protocol — Handoff Document
## Sessão: Março 5, 2026 — Para o próximo chat

---

## ESTADO ACTUAL DO PROJECTO

### Protocolo
- **Nome:** Yelden Protocol
- **Whitepaper:** v14 — github.com/yeldenfund/yelden-protocol
- **Site:** yelden.fund
- **X:** @yeldenfund
- **Telegram:** t.me/yeldenfund
- **Email:** yeldenfund@gmail.com / hello@yelden.fund

### Contratos Deployados (Sepolia Testnet)
- **YeldenVault (ERC-4626):** 182 testes, Certora 7/7, Echidna 3/3
- **AIAgentRegistry v3:** 69 testes, Certora 7/7, Echidna 3/3
- **ZKVerifier (Groth16):** 16 testes, 532 constraints, trusted setup completo
- **YeldenDistributor:** 12 testes
- **$YLD Token:** deployado 0x72D6971A...
- **AIAgentRegistry:** 0xca380aC622d775f32A31fB9a23a17E1eEBF3A22d7
- **Total:** 198 testes passando, 0 falhando

---

## LIVE TEST — MARKOWITZ TRADING BOT

### Dados actuais (Mar 5, 2026)
- **Conta MT5:** 61482544 DEMO (Pepperstone)
- **Balance:** $10,650.33
- **Trades fechados:** 46 (Feb 24 → Mar 4)
- **Win rate:** 67.4%
- **Lucro total:** $+666.74
- **Score acumulado:** 886/1000 (F2 + 60-day decay)
- **Wallet agente:** 0xfD3d7fdda54360dc29caa2f746ad77278a266cfc

### Pipeline Autónomo (VPS FXVM)
```
MT5 → mt5_monitor.py → agent_performance.json
  ↓
yelden_reporter.py → AIAgentRegistry Sepolia → submission_receipt.json
  ↓
telegram_report.py → @yeldenfund (daily 06:00 UTC)
```

### On-Chain Submissions (6 confirmadas)
- 0x1c17f74... Mar 01, 8 trades, score 966
- 0xe4ac05... Mar 02, 1 trade, score 764
- 0x9c0358... Mar 02, 18 trades, score 958
- 0xa62640... Mar 03, 20 trades, score 962
- 0x63f995... Mar 04, 19 trades, score 927
- 0x7d7dc4... Mar 04, 12 trades, score 802

### ERC-8004 Registry
- **Agent ID:** #27703 (BNB Smart Chain)
- **8004scan:** 8004scan.io/agents/bnb/27703
- **Status:** Active

---

## WEBSITE — yelden.fund

### Tema WordPress v4 (ACTUAL)
- **front-page.php** — landing page principal
- **agent-dashboard.php** — página /agent com dashboard live
- **Whitepaper link** → GitHub PDF directo
- **Nav:** Protocol | AI Economy | UBI Sim | FAQ | Live Agent | GitHub

### Dashboard /agent
- Score acumulado 886 em destaque (Bebas Neue, grande, dourado)
- Score batch 802 secundário
- 6 métricas: Return %, Win Rate, Sharpe, Max DD %, Avg R, Trades
- Gráfico canvas — evolução dos 6 runs
- Tabela histórico com coluna Δ
- 6 transações Sepolia com links Etherscan
- ERC-8004 badge #27703

---

## SCORE FORMULA — F2 + 60-DAY DECAY

```python
# Peso por run
peso = n_trades × exp(-0.693 × days_ago / 60)

# Score acumulado
accumulated = Σ(score_i × peso_i) / Σ(peso_i)
```

---

## AGENTPROOF — ANÁLISE

### O que são
- Trust Oracle para ERC-8004
- 51k+ agents, 150k+ avaliações
- Composite score 0-100, Bayesian smoothing de 6-8 sinais
- Tiers: Bronze → Diamond
- Primeiros a escrever feedback on-chain na Solana (29 agents)
- BuilderBen (@BuilderBenv1) é o criador — já leu o repo Yelden

### Score estimado do Markowitz bot na AgentProof
- Rating (Bayesian): 64.3/100
- Volume: 61.9/100
- Consistency: **81.4/100** (ponto forte)
- Validation Rate: 66.7/100
- Age: **39.0/100** (só 9 dias — principal limitação)
- Uptime: 85.0/100
- **COMPOSITE: 65.4/100 — Tier Gold**
- Média da rede: 49.9-53.9

### Whitepaper AgentProof
- Está em download local (Paulo tem o PDF)
- Não foi lido ainda — próxima prioridade
- URL: agentproof.sh/whitepaper

### Posicionamento
- AgentProof = "Quem o agent é" (identidade, reputação, presença)
- Yelden = "O que o agent arrisca" (performance, consequência económica)
- **Complementares, não concorrentes**
- Integração potencial: AgentProof → SCORER_ROLE → AIAgentRegistry

---

## V2 TECHNICAL DESIGN — OPEN PROBLEMS

### The Blade That Cuts Both Ways (Open Problem 6)
O problema mais crítico não resolvido:
- Stake fixo em YLD: token aprecia → barreira sobe (plutocracy)
- Stake fixo em YLD: token deprecia → skin evaporates (accountability collapses)
- Numerai descobriu isto empiricamente em 7 anos

**Proposta de fases:**
- Phase 1: 50 YLD fixo (launch)
- Phase 2: max(50 YLD, AUM × 0.5%)
- Phase 3: USD-denominated, YLD quantity auto-adjusts

### Outros Open Problems V2
1. scoreOf() como primitive (BuilderBen feedback)
2. VerificationTier (3 tiers: ON_CHAIN, DON_VERIFIED, DISPUTE_RESOLVED)
3. contestSlash() com ZK proof
4. registerWithProvenHistory() — bootstrap score
5. Protocol integration incentive layer

**Documento:** AIAgentRegistry_V2_Design.docx (gerado nesta sessão)

---

## X — THREADS PUBLICADOS

### "Dynamic Skin in the Game" (Mar 5, 2026)
- 7 posts publicados
- Conceito central: stake fixo em token nativo é broken
- Proposta: stake ajustado por track record
- Termina: "the co-founder we're looking for needs skin in the game too. yelden.fund"

### Axiom VI
"Accountability without symmetric economic exposure is cosmetic.
True accountability requires structural symmetry between gain and loss.
Where the blade cuts only one way, collapse is not a risk — it is a certainty."

---

## OUTREACH ACTIVO

### BuilderBen (@BuilderBenv1)
- Criador do AgentProof
- Respondeu positivamente ao repo
- Feedback incorporado: isEligible() como helper, não primitive
- Próximo passo: DM técnico sobre integração SCORER_ROLE
- Status: sem resposta recente

### ERC-8004 Builders Group (Telegram)
- Grupo activo com Oya, Prutopia (Luciano), agentaOS
- Markowitz bot registado como #27703
- Comentários postados mas sem resposta ainda
- Luciano (Prutopia) — 20k profissionais, Job Profile for agents — DM pendente

### Outros targets
- @SEVEN (RWAFi score bands) — comentário postado
- @Butler_Agent (ACP portable reputation) — comentário postado
- ZeMariaMacedo — monitoring

---

## PRÓXIMAS PRIORIDADES

1. **Ler whitepaper AgentProof** — Paulo tem o PDF, mandar em nova conversa
2. **DM Luciano (Prutopia)** — integração work history + AIAgentRegistry
3. **DM Oya** — commitment agent + accountability scoring
4. **Actualizar dashboard** com dados de Mar 5 (46 trades, $666.74)
5. **Publicar no grupo ERC-8004** — link para 8004scan #27703
6. **Responder BuilderBen** quando ele responder
7. **V2 design** — decisão sobre stake Phase 2 (aguarda co-founder)

---

## FICHEIROS IMPORTANTES (outputs desta sessão)
- yelden-theme-v4.zip — tema WordPress actual
- dashboard.html — dashboard standalone
- AIAgentRegistry_V2_Design.docx — documento técnico V2
- markowitz-trading-bot-metadata.json — ERC-8004 metadata corrigido

---

## TRANSCRIPT DESTA SESSÃO
/mnt/transcripts/2026-03-05-01-38-09-telegram-integration-trade-audit-dashboard-v2.txt

## TODOS OS TRANSCRIPTS
/mnt/transcripts/journal.txt

---
*Documento gerado automaticamente — Março 5, 2026*
*Para continuar: abre nova conversa, anexa este ficheiro, e continua*
