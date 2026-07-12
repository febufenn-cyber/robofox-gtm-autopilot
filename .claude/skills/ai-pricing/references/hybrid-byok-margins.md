# AI pricing — hybrid models, BYOK, and margins

Upstream detail moved here to keep `SKILL.md` below 500 lines.

## Hybrid Pricing Model Design

Pure pricing models have weaknesses. Consumption scares buyers. Per-seat misses expansion. Outcome puts all risk on you. Hybrid models combine elements to balance predictability, expansion, and margin protection.

**The hybrid formula:**

```
Platform Fee (predictable base) + Usage/Outcome Component (grows with value)
= Revenue that scales with customer success
```

**Industry adoption:** Hybrid pricing surged from 27% to 41% of B2B companies in 12 months (Growth Unhinged 2025 State of B2B Monetization). Pure per-seat dropped from 21% to 15% in the same period.

### Hybrid Model Patterns

| Pattern | Structure | Example | When to Use |
|---|---|---|---|
| Base + consumption | Platform fee + per-unit overage | $99/mo + $0.05/API call over 10K | API/platform products with variable usage |
| Base + credits | Platform fee + credit allocation | $199/mo includes 1,000 credits, $0.15/credit after | Multi-feature products with different cost profiles |
| Base + outcome | Platform fee + per-outcome | $499/mo + $0.99/resolved ticket | Agent products with measurable outcomes |
| Seat + consumption | Per-seat + usage cap/overage | $30/seat/mo + credits for AI actions | Copilots with heavy AI features |
| Commitment + burst | Annual commit + on-demand pricing | $50K/yr commit + pay-as-you-go above | Enterprise deals needing budget predictability |

### Designing Your Hybrid Model

```
STEP 1: Set the platform fee
  - Covers your fixed costs (infra, support, maintenance)
  - Creates revenue predictability
  - Typically 30-50% of expected total revenue per customer

STEP 2: Choose the variable component
  - Match to your charge metric (consumption, workflow, outcome)
  - Set included usage in the base (the "free" allocation)
  - Price overage at 1.2-2x your unit cost

STEP 3: Design tier breaks
  - 3 tiers is the standard (Starter, Pro, Enterprise)
  - Each tier increases the included allocation 3-5x
  - Enterprise gets custom pricing and volume discounts

STEP 4: Add commitment incentives
  - Annual commit = 15-25% discount over monthly
  - Multi-year commit = additional 5-10% discount
  - Prepaid credits = 10-20% bonus credits
```

### Hybrid Pricing Example (AI Support Agent)

| Component | Starter | Pro | Enterprise |
|---|---|---|---|
| Monthly platform fee | $199/mo | $599/mo | Custom |
| Included resolutions | 200/mo | 1,000/mo | Custom |
| Overage per resolution | $1.29 | $0.89 | $0.49-0.69 |
| Channels | Chat only | Chat + email | All channels |
| SLA | Best effort | 99.5% uptime | 99.9% + dedicated CSM |
| Annual discount | 15% | 20% | Negotiated |

## BYOK (Bring Your Own Key) Pricing

BYOK lets customers plug in their own LLM API keys. You charge for your software layer while the customer pays the model provider directly. This decouples your pricing from volatile model costs.

### BYOK Decision Framework

| Factor | BYOK Wins | Managed Model Wins |
|---|---|---|
| Customer type | Enterprise with existing model contracts, developers | SMB, non-technical buyer |
| Model preference | Customer insists on specific provider (compliance, existing deal) | Customer trusts your model selection |
| Margin goal | Higher software margin (no COGS on model costs) | Higher total revenue (markup on model usage) |
| Pricing simplicity | Customer comfortable with two bills | Customer wants one price for everything |
| Support burden | Lower (model issues go to provider) | Higher (you own the full stack) |
| Switching cost | Lower (customer can swap your tool, keep model) | Higher (bundled = stickier) |
| Data sensitivity | Customer needs data to stay in their cloud/account | Customer trusts your data handling |

### BYOK Pricing Structure

| Component | What You Charge | Example |
|---|---|---|
| Software license | Monthly/annual fee for your platform | $49-299/mo per seat or workspace |
| Model costs | Nothing (customer pays provider directly) | Customer pays OpenAI/Anthropic/Google |
| Premium features | Add-on fees for orchestration, analytics, fine-tuning | $99/mo for advanced routing, $199/mo for analytics |
| Support tier | Tiered support pricing | Free community, $99/mo priority, custom enterprise |

**Real BYOK examples:**
- JetBrains AI: BYOK available for AI chat and agents, supports Anthropic, OpenAI, and compatible providers
- OpenRouter: 5% usage fee on provider costs when routing through your own keys
- Cursor: BYOK option lets developers use their own API keys, lower subscription tier

### When NOT to Offer BYOK

- Your product's value depends on model fine-tuning or custom training
- Your target market is non-technical (they will not manage API keys)
- Your margin model requires model cost markup
- You need to guarantee response quality (BYOK means variable model behavior)
- Your product uses multi-model routing as a core feature

## Margin Management for AI Products

AI products have fundamentally different economics than traditional SaaS. Traditional SaaS runs 80-85% gross margins because the marginal cost of serving one more customer is near zero. AI products incur real compute costs for every request.

### Margin Landscape

| Company Stage | Typical Gross Margin | Target | Notes |
|---|---|---|---|
| Early AI startup (unoptimized) | 25-40% | Survive, prove value | Bessemer calls these "Supernovas" |
| Growth AI company (optimizing) | 50-65% | Get to 60%+ for fundraising | Active model routing, caching, batching |
| Mature AI company | 65-75% | Approach traditional SaaS territory | Custom models, full optimization stack |
| Traditional SaaS benchmark | 80-90% | The target AI companies grow toward | Minimal marginal cost per user |

**Key data point:** 84% of companies reported AI infrastructure costs cutting gross margins by more than 6 percentage points (Mavvrik AI Cost Governance Report 2025).

### Unit Economics You Must Track

| Metric | Definition | Target | How to Calculate |
|---|---|---|---|
| CPT (Cost Per Task) | Total AI cost to complete one unit of work | Varies by task | Model cost + compute + orchestration / tasks completed |
| CPR (Cost Per Resolution) | Cost to achieve one customer outcome | Less than 30% of price charged | All AI costs for resolved outcomes / resolutions |
| CPAM (Cost Per Active Member) | AI spend per active user per month | Less than 20% of ARPU | Total AI infrastructure / monthly active users |
| Token efficiency | Tokens consumed per task vs. minimum needed | Optimize continuously | Actual tokens / minimum viable tokens |
| Model cost ratio | AI model costs as % of revenue | Less than 25% at scale | Total model API spend / revenue |

### The Margin Improvement Stack

Seven levers to improve AI product margins, ordered by typical impact.

| Lever | Margin Impact | Implementation Effort | How It Works |
|---|---|---|---|
| Model routing | 50-98% cost reduction on routed tasks | Medium | Route simple tasks to cheaper/smaller models, reserve frontier models for complex tasks |
| Prompt caching | 45-80% reduction on repeated prompts | Low | Cache common prompt prefixes; Anthropic caching costs 90% less, OpenAI 50% less |
| Batch processing | 50% cost reduction on batch-eligible tasks | Low | Use batch APIs for non-real-time work; guaranteed 50% savings on most providers |
| Fine-tuned small models | 60-80% cost reduction vs. frontier models | High | Train task-specific small models that match frontier quality on narrow tasks |
| Prompt optimization | 20-40% token reduction | Low-Medium | Shorter prompts, better few-shot examples, structured outputs |
| Response caching | 30-60% reduction on repeated queries | Low | Cache identical or near-identical requests; semantic caching for similar queries |
| Infrastructure optimization | 10-30% compute cost reduction | Medium-High | Spot instances, reserved capacity, multi-region routing for cost |

### Model Routing in Practice

```
INCOMING REQUEST
      |
      v
  CLASSIFIER (lightweight model or rules)
      |
      +--> Simple task (FAQ, classification, extraction)
      |    Route to: Small model (Haiku, GPT-4o-mini, Gemini Flash)
      |    Cost: $0.0001-0.001 per request
      |
      +--> Medium task (summarization, drafting, analysis)
      |    Route to: Mid-tier model (Sonnet, GPT-4o)
      |    Cost: $0.001-0.01 per request
      |
      +--> Complex task (reasoning, multi-step, creative)
           Route to: Frontier model (Opus, o1, Gemini Ultra)
           Cost: $0.01-0.10 per request

RESULT: 70-80% of tasks route to cheapest tier
        Average cost drops 60-80%
```

### Margin Improvement Roadmap

| Phase | Timeline | Actions | Expected Margin |
|---|---|---|---|
| 1. Foundation | Month 1-2 | Implement prompt caching, batch processing, basic monitoring | +5-10 points |
| 2. Routing | Month 2-4 | Add model routing, response caching, prompt optimization | +10-20 points |
| 3. Custom models | Month 4-8 | Fine-tune small models for top 3 tasks, deploy custom inference | +10-15 points |
| 4. Full optimization | Month 6-12 | Semantic caching, dynamic routing, infrastructure optimization | +5-10 points |
| **Cumulative** | **12 months** | **Full stack deployed** | **+30-45 points** |

### Cost Projection Model

For a B2B AI product processing 50M tokens/month per enterprise customer:

| Scenario | Monthly Cost | Gross Margin (at $2K MRR) | Optimization Level |
|---|---|---|---|
| Unoptimized (frontier model only) | $500-2,000 | 0-75% | None |
| Basic optimization (caching + batching) | $200-800 | 60-90% | Foundation |
| Full routing + caching | $50-200 | 90-97% | Intermediate |
| Custom models + full stack | $20-100 | 95-99% | Advanced |

**Key insight:** AI compute costs are falling roughly 10x every 3 years. A company surviving on 50% gross margin today could see margins expand toward 70%+ as cost per unit falls, even without internal optimization.

