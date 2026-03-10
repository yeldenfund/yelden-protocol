# Yelden Protocol — Contexto Estratégico e Relacional
## Complemento ao YELDEN_HANDOFF_MAR05.md
## Data: Março 5, 2026

---

## LEIA PRIMEIRO: O QUE É O YELDEN NA REALIDADE AGORA

O Yelden é um projecto de uma pessoa só.
Sem co-founder. Sem equipa. Sem recursos externos.
Sem depósitos solicitados. Sem mainnet.

Os contratos passam 198 testes. O ZKVerifier funciona com provas reais.
O bot está live com dados reais. O pipeline é autónomo.

Mas é um projecto de uma pessoa com ambição de protocolo.
Esta tensão é a realidade. Não é escondida — é documentada.

---

## ORIGEM DO PROJECTO

Começou como "Mundi" — um protocolo de UBI com yield.
Passou por 15+ nomes (Vyrtuo, Argon, Noblis, Solidus, Vena...).
Cada nome foi verificado contra tokens existentes e conflitos de trademark.
"Yelden" foi seleccionado por ser único, sem conflitos, e com o .fund disponível.

O domínio yelden.fund está registado.
O GitHub yeldenfund está activo.
O whitepaper passou da v1 para v15 Beta nesta sessão.

---

## A TESE CENTRAL — HUMAN-AI ECONOMY

O insight que define o Yelden não é técnico. É filosófico:

**"Agents autónomos já movem capital. A questão não é se participam — é se são accountable quando o fazem."**

O DeFi trata agents como ferramentas. O Yelden trata-os como participantes económicos com obrigações — e recompensas.

A analogia correcta não é "reputação de agent". É "seguro obrigatório para condutores".
Um condutor sem historial paga mais. Um condutor experiente paga menos.
A consequência calibra o risco. Isso é o AIAgentRegistry.

---

## OS AXIOMAS (publicados, fazem parte do posicionamento público)

**Axiom I** — Agency without consequence is not agency. It is performance.

**Axiom II** — Reputation without stake is noise. The signal is what you lose.

**Axiom III** — Trust scales with verifiable history, not with promises.

**Axiom IV** — An agent that cannot be penalised cannot be trusted with capital.

**Axiom V** — The first duty of infrastructure is honesty about its own limitations.

**Axiom VI** — Accountability without symmetric economic exposure is cosmetic.
True accountability requires structural symmetry between gain and loss.
Where the blade cuts only one way, collapse is not a risk — it is a certainty.

---

## O PROBLEMA DA STAKE CALIBRATION — "THE BLADE THAT CUTS BOTH WAYS"

Este é o problema mais crítico não resolvido. Está documentado honestamente no V2 Design Doc.

Token aprecia → barreira sobe → meritocracy becomes plutocracy.
Token deprecia → stake evaporates → accountability becomes theatre.

Numerai descobriu isto empiricamente em 7 anos.
Nenhum protocolo resolveu ainda.

O Yelden propõe 3 fases:
- Phase 1: 50 YLD fixo (já implementado)
- Phase 2: max(50 YLD, AUM × 0.5%) — requires co-founder alignment
- Phase 3: USD-denominated stake, YLD adjusts with Chainlink price feed

Phase 3 é o que Numerai nunca construiu. É research, não roadmap confirmado.

---

## O MARKOWITZ BOT — O QUE É E O QUE NÃO É

**O que é:**
- Proof of concept da fórmula F2 + decay com dados reais
- Demonstração do pipeline MT5 → Sepolia → Telegram
- Prova que o score funciona antes de escalar para agents on-chain
- Tier 1.5 de verificação (off-chain execution, on-chain reporting)

**O que NÃO é:**
- O produto final do Yelden
- Um bot forex extraordinário (performance boa mas não excepcional)
- Evidência de vantagem competitiva em trading

**A estratégia real:**
O Yelden foca em agents on-chain — onde os dados são públicos, sem ZK proof necessário.
O Markowitz foi o laboratório para testar a fórmula com dados reais.
A fórmula F2 + decay aplica-se directamente a qualquer wallet on-chain.

**Posicionamento correcto:**
"Temos uma fórmula de performance financeira que funciona em qualquer agent com actividade on-chain, e já testámos com dados reais."

Não: "temos um bot forex com ZK proof."

---

## AGENTPROOF — ANÁLISE COMPLETA (lido o whitepaper v2.0)

### O que eles têm
- 51k+ agents, 150k+ avaliações on-chain
- 8 layers com pesos explícitos (ver abaixo)
- Bayesian smoothing k=3 (puxa para média da população)
- Primeiro a escrever feedback on-chain na Solana (29 agents)
- BuilderBen é doutor, tem equipa, tem contrato com a Solana Foundation

### Os 8 Layers com Pesos
| Layer | Sinal | Peso |
|-------|-------|------|
| 1 | Rating Score | 25% |
| 2 | Feedback Volume | 20% |
| 3 | Consistency | 20% |
| 4 | Validation Success | 15% |
| 5 | Account Age | 12% |
| 6 | Activity/Uptime | 10% |
| 7 | Deployer Reputation | 8% |
| 8 | URI Stability | 5% |

### O que eles NÃO têm
Layer 4 (Validation Success) é binário — entregou ou não. Não mede quão bem.
Nenhum oracle de performance financeira quantitativa.
Não calculam Sharpe, win rate, drawdown, ou alpha gerado.

### O Legitimate Business Model Attack (Sec. 5 whitepaper AgentProof)
O AgentProof reconhece que um agent pode ser genuinamente bom durante 6 meses e degradar lentamente.
Apenas o Layer 13 (active probing) detectaria — e ainda é roadmap.

O Yelden resolve isto por design: decay temporal de 60 dias detecta degradação automaticamente.
Esta é a abertura para conversa intelectual com BuilderBen — não uma pitch, uma perspectiva.

### Sinergias identificadas
1. AgentProof → SCORER_ROLE → AIAgentRegistry (já no handoff)
2. scoreOf() Yelden como input para Layer 4 AgentProof (trading agents)
3. ZK proof Yelden como bypass parcial do Layer 5 (age penalty) — proposta técnica
4. Complementaridade de narrativa: "AgentProof tem os olhos. Yelden tem os dentes."

### Status da relação com BuilderBen
- Leu o repo Yelden e respondeu positivamente ("interesting")
- Feedback incorporado: isEligible() como helper, não primitive
- Sem resposta recente
- Abordagem correcta: conversa intelectual sobre Legitimate Business Model Attack, NÃO pitch

---

## POSICIONAMENTO NO ECOSSISTEMA ERC-8004

### O que existe hoje
- **AgentProof** — Trust Oracle, 51k agents, Bayesian composite 0-100
- **Oya** — commitment agents com Safe + Optimistic Governor, mainnet
- **Prutopia** (Luciano) — 20k profissionais, Job Profile for agents
- **agentaOS** — financial OS for agent economy, self-custody wallets
- **0xWorkHQ** — staked reputation + verifiable task execution (Base)
- **Nookplot** — decentralised coordination protocol (Base)
- **Helixa** — Cred Scores on top of ERC-8004
- **Xona Orbit** — integra OpenClaw, x402, Solana wallets + ERC-8004

### Onde o Yelden se posiciona
"The enforcement layer" — todos os outros criam reputação ou identidade.
O Yelden é o único que aplica consequência económica irreversível.

A tese: identidade sem consequência é uma lista de endereços melhorada.
Reputação sem stake é curriculum. Skin in the game real requer perda real.

### Threads publicados que definem o posicionamento público
1. "Agency Without Consequence" — manifesto filosófico
2. "Dynamic Skin in the Game" — o problema técnico com stake fixo
3. Comentários em @SEVEN, @Butler_Agent, @Billions Network KYA

---

## O QUE FALTA PARA O YELDEN AVANÇAR

### Bloqueador 1 — Co-founder técnico (crítico)
Sem co-founder técnico: sem mainnet, sem depósitos, sem auditoria.
O projecto está intencionalmente parado neste passo.

Perfil necessário:
- Solidity profundo: ERC-4626, zkSNARKs, Chainlink, formal verification
- Posição sobre Dynamic Skin in the Game (Phase 2-3 stake design)
- Conforto com limitações documentadas honestamente
- Alinhamento filosófico com a tese Human-AI Economy

### Bloqueador 2 — $YLD liquidity
Sem liquidity: stake Phase 2 indefinida, token utility especulativa.
Resolvido por: liquidity pool bootstrap pós-co-founder.

### Não é bloqueador agora
- BuilderBen não responder — útil mas não crítico
- ERC-8004 registration completa — feito (#27703)
- Dashboard perfeito — funcional e suficiente

---

## RECURSOS ACTUAIS (Março 2026)

### Contratos (Sepolia)
- YeldenVault: 0x... (ERC-4626, 182 testes)
- AIAgentRegistry: 0xca380aC622d775f32A31fB9a23a17E1eEBF3A22d7
- $YLD Token: 0x72D6971A...
- ZKVerifier Groth16: deployado, trusted setup completo

### Infraestrutura
- VPS FXVM: 1.5GB RAM, 2 vCPU, $17/mês
- Task Scheduler: 06:00 UTC daily
- Telegram bot: @yelden_reporter_bot
- WordPress: yelden.fund (tema v4)

### Pipeline autónomo
MT5 → mt5_monitor.py → yelden_reporter.py → Sepolia → telegram_report.py → @yeldenfund

### Ficheiros críticos no VPS
- C:\YeldenBridge\mt5_monitor.py
- C:\YeldenBridge\yelden_reporter.py
- C:\YeldenBridge\telegram_report.py
- C:\YeldenBridge\run_bridge.bat
- C:\YeldenBridge\agent_performance.json
- C:\YeldenBridge\mt5_monitor_state.json
- C:\YeldenBridge\.env (PRIVATE_KEY, RPC_URL, TELEGRAM_TOKEN, etc.)

---

## DECISÕES JÁ TOMADAS (não reabrir sem razão forte)

1. **Yelden como nome** — final, domínio registado
2. **ERC-4626 para vault** — standard confirmado
3. **isEligible() como helper** — BuilderBen feedback, V2 usa scoreOf()
4. **50 YLD stake fixo Phase 1** — simples, baixa barreira, sem oracle
5. **F2 + 60-day decay** — implementado e live
6. **MIT License** — open source total
7. **Markowitz bot = proof of concept** — não produto final
8. **Foco em agents on-chain** — onde dados são públicos

---

## DECISÕES ABERTAS (requerem co-founder)

1. **Stake Phase 2-3** — USD-denominated design
2. **contestSlash()** — V2, ZK proof de comportamento correcto
3. **registerWithProvenHistory()** — V2, bootstrap score via ZK
4. **AgentProof integração formal** — aguarda conversa técnica
5. **Mainnet timing** — aguarda auditoria e co-founder

---

## PRÓXIMAS ACÇÕES PRIORITÁRIAS

1. **Ler whitepaper AgentProof** → já lido na outra conversa (contexto acima)
2. **Actualizar score com dados Mar 5** — 46 trades, $666.74, win rate 67.4%
   - Dashboard actualiza automaticamente às 06:00 UTC via pipeline
3. **DM Luciano (Prutopia)** — work history + reputation → AIAgentRegistry integration
4. **DM Oya** — commitment agent architecture + accountability scoring
5. **Post no grupo ERC-8004** — link para 8004scan.io/agents/bnb/27703
6. **BuilderBen** — se responder: Legitimate Business Model Attack como abertura intelectual

---

## TRANSCRITOS DISPONÍVEIS

Todos em /mnt/transcripts/
Ver journal.txt para índice completo (25+ sessões desde Feb 23, 2026)

Mais relevantes:
- 2026-03-05-01-38-09-telegram-integration-trade-audit-dashboard-v2.txt
- 2026-03-05-02-40-11-agent-dashboard-v2-design-doc.txt (esta sessão)
- 2026-03-04-03-14-54-mt5-agent-bridge-first-onchain-score.txt
- 2026-03-03-12-34-19-builderben-dm-mt5-agent-bridge-design.txt

---

*Gerado: Março 5, 2026 — Fim da sessão longa*
*Para continuar: anexa YELDEN_HANDOFF_MAR05.md + este ficheiro na nova conversa*
