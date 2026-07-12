---
name: ai-pricing
description: "When the user wants to price an AI product, choose a charge metric, design pricing tiers, test a pricing hypothesis, or protect AI gross margins. Also triggers on 'AI pricing,' 'usage-based pricing,' 'outcome pricing,' 'workflow pricing,' 'credits,' 'BYOK,' 'pricing tiers,' and 'AI margins.' Do NOT use for channel selection, live ad changes, or presenting an untested price as validated."
---

# AI Pricing

Design pricing around buyer value, measurable units, delivery economics, and the current sales motion. Treat every early-stage price as a hypothesis until customer evidence exists.

## Required context

Read the relevant `context/products/*.md` file, then establish:

- Product archetype: copilot, autonomous agent, AI-enabled service, or API/platform.
- Economic buyer and current alternative.
- Human or software cost replaced.
- Sales motion and expected implementation effort.
- Variable AI and support cost per customer/task.
- Whether outcomes are measurable and attributable.
- Existing contracts or migration constraints.

Missing facts must be marked `[UNVERIFIED]`.

## Charge-metric decision table

| IF | THEN use | Reason |
|---|---|---|
| A specific business outcome is measurable and attributable | Outcome pricing | Aligns price to completed value. |
| Work occurs in discrete countable tasks but outcomes have shared attribution | Workflow pricing | Bills for completed work without attribution disputes. |
| Buyer is technical and consumes an API or compute resource | Consumption pricing | Gives transparent control over raw use. |
| Multiple task types have different costs | Credits | Abstracts model costs and permits packaging changes. |
| Buyer needs predictability but value grows with usage | Hybrid base + variable | Protects a revenue floor while retaining expansion. |
| Product is an AI-enabled managed service | Setup/project fee + retainer + scoped overage | Reflects implementation and ongoing delivery. |

Avoid raw token pricing for non-technical business buyers.

## Product-archetype defaults

| Archetype | Default model | Expansion lever | Main risk |
|---|---|---|---|
| Copilot augmenting a human | Per seat or seat + credits | More seats and higher use | Heavy users can destroy margin. |
| Agent replacing a task | Per workflow or outcome | More task types and volume | Outcome definition disputes. |
| AI-enabled service | Setup/project + retainer | More workflows, locations, or deliverables | Unbounded custom work. |
| API/platform | Usage or committed usage | Higher volume and commitment | Bill shock and low predictability. |

## Hybrid pricing design

Use:

`Platform fee + included allowance + variable overage`

The platform fee should cover predictable implementation, support, and infrastructure. The included allowance proves value without creating unlimited liability. Overage should map to a buyer-understandable unit.

See `references/hybrid-byok-margins.md` for BYOK decisions, margin targets, routing, caching, and cost controls.

## Early-stage service packaging

For pre-first-10-customer products:

1. Keep one primary offer and at most one higher-touch option.
2. Separate setup/implementation from recurring operations.
3. Define exactly what the retainer includes: locations, call minutes, workflows, languages, integrations, support, and reporting.
4. State overage or out-of-scope work before delivery.
5. Mark the price `untested` until paid evidence exists.
6. Do not discount without receiving something measurable in return, such as faster payment, reduced scope, case-study permission, or longer commitment.

## Willingness-to-pay validation

Use conversations, proposals, and paid pilots—not opinions alone.

| Evidence | Strength |
|---|---|
| Paid contract at the proposed price | Strongest |
| Signed pilot with defined conversion terms | Strong |
| Proposal accepted pending procurement | Moderate |
| Buyer compares price with current cost and continues evaluation | Useful |
| “Sounds reasonable” without commitment | Weak |
| Founder intuition or competitor list price alone | Not validation |

Track objections by segment, buyer, geography, scope, price, and alternative.

## Margin guardrails

Calculate:

- Gross margin per customer.
- Cost per completed workflow/outcome.
- Model cost as a percentage of revenue.
- Founder/support hours required per account.
- Expected payback on setup work.

Do not offer unlimited AI usage unless a hard fair-use ceiling and repricing mechanism exist. Prefer model routing, prompt caching, batch processing, and response caching before reducing customer value.

## BYOK rule

Offer BYOK only when the target buyer can manage provider keys and it materially helps compliance, procurement, model preference, or margin. Do not add BYOK reactively if it weakens quality control or confuses the buyer.

## Tier design

Default to three tiers only when there are genuinely three buyer/use patterns. Otherwise begin with one offer plus custom enterprise scope.

Possible gates:

- Included usage/workflows.
- Locations or business units.
- Languages/channels.
- Integrations.
- Analytics and audit logs.
- Support/SLA.
- Model quality or latency.

Never manufacture a tier using low-value feature padding.

## Pricing output contract

A pricing recommendation must include:

1. Product archetype and buyer.
2. Recommended charge metric and rejected alternatives.
3. Packaging structure.
4. Unit-economics assumptions, each labeled verified or `[UNVERIFIED]`.
5. Scope and overage boundaries.
6. Validation plan and evidence threshold.
7. Margin risks and mitigation.
8. Migration plan when replacing existing pricing.

See `references/migration-competitive-analysis.md` for grandfathering and migration.

## Robofox guardrails

- Keep `pricing_hypothesis` explicitly untested until paid evidence exists.
- Never alter CRM records, invoices, ads, or contracts automatically.
- Do not invent competitor pricing or industry benchmarks.
- Use founder-approved proposals and drafts only.
- When pricing informs channel selection, defer to `channel-portfolio-selector`.
