---
name: positioning-icp
description: "When the user wants to define an ideal customer profile, position an AI product, build messaging, identify an economic buyer, or validate product-market fit. Also triggers on 'ICP,' 'ideal customer profile,' 'positioning,' 'buyer persona,' 'PMF,' 'messaging,' and 'competitive positioning.' Do NOT use for choosing a channel portfolio, auto-sending outreach, or inventing customer proof."
---

# Positioning and ICP for AI Products

Turn technical capability into a buyer-specific business case. Use shared product context and customer evidence; never present a model name or generic AI capability as the primary value proposition.

## Required context

Read the relevant `context/products/*.md` file and establish:

- What the product does today, not the roadmap.
- Current target geography and segment.
- Economic buyer, user, champion, and blocker.
- Current alternative: staff, missed work, agency, incumbent software, or doing nothing.
- Trigger that makes the problem urgent.
- Current pricing hypothesis and sales motion.
- Existing proof and its sample size.

Mark missing information `[UNVERIFIED]`.

## Four-layer positioning stack

| Layer | Question | Output |
|---|---|---|
| Category | What budget/problem category does the buyer already understand? | Familiar market anchor. |
| Wedge | Where is this product materially better for a narrow segment? | Specific differentiated capability. |
| Proof vector | What evidence supports the wedge? | Paid result, measured pilot, or clearly labeled hypothesis. |
| Alternative framing | What would the buyer otherwise use? | Honest comparison against the real alternative. |

Template:

> For [specific segment] experiencing [trigger/problem], [product] is a [known category] that [business outcome/wedge], unlike [real alternative], which [relevant limitation]. Evidence: [proof or UNVERIFIED hypothesis].

## ICP dimensions

Keep fit and intent separate.

### Fit

- Industry/use case.
- Company/location size.
- Operational pain frequency.
- Language and channel requirements.
- Ability to implement and pay.
- Compliance or integration constraints.

### Intent

- Active hiring for the problem.
- Expansion/new location.
- Missed-call or response-time pain.
- Current vendor dissatisfaction.
- Referral or founder relationship.
- Pricing/demo-page engagement.

| Fit | Intent | Action |
|---|---|---|
| High | High | Founder activates immediately. |
| High | Low | Nurture and wait for a trigger. |
| Low | High | Investigate possible ICP drift; do not force-fit. |
| Low | Low | Disqualify. |

## Pre-customer ICP method

When there are fewer than 10 paying customers:

1. Start with a narrow hypothesis, not a universal persona.
2. Interview owners/operators about the current workflow and cost of failure.
3. Test clinics and coaching centres as separate segments.
4. Record trigger, objection, alternative, decision process, and willingness to pay.
5. Do not build scoring weights from fictional historical data.
6. Update the ICP after every five meaningful owner conversations or first three paid wins.

## Capability-to-outcome translation

| Technical statement | Buyer-level translation |
|---|---|
| Tamil and English speech pipeline | Handles common caller language without forcing English-only service. |
| Automated call answering | Reduces missed enquiries when staff are busy or unavailable. |
| CRM/WhatsApp integration | Captures and routes follow-up without manual re-entry. |
| Model orchestration | Not a headline; translate into reliability, quality, or cost. |

Do not claim quantified savings, accuracy, conversion, or revenue lift without evidence.

## Messaging architecture

| Tier | Audience | Content |
|---|---|---|
| Strategic narrative | Owner/C-suite | Why the operational problem matters now. |
| Value proposition | Economic buyer | Business outcome, urgency, implementation burden, proof. |
| Evaluation detail | Champion/evaluator | Workflow, integrations, controls, limits, and honest gaps. |

Validation checks:

- Specific to one buyer and situation.
- Cannot be copied unchanged by every competitor.
- Uses buyer language from conversations.
- Separates proof from hypothesis.
- Matches the audience’s altitude.

## Competitive alternatives

Always include:

- Doing nothing and accepting missed opportunities.
- Receptionist/front-desk staff.
- Shared call centre or agency.
- Generic IVR/telephony.
- Other AI voice-agent providers.
- Internal/manual WhatsApp follow-up.

Position against total workflow cost and outcome, not merely feature count.

## Deliverables

Depending on the request, produce:

1. One-sentence ICP.
2. Economic buyer/user/champion map.
3. Trigger and disqualifier table.
4. Four-layer positioning stack.
5. Tiered messaging.
6. Proof gaps and validation interviews.
7. Updated context recommendations without silently editing the context file.

## Robofox guardrails

- Keep clinic and coaching-centre evidence separate until data supports combining them.
- Treat Madurai/Tamil Nadu as the initial geography, not proof of all-India fit.
- Never invent testimonials, customer counts, savings, or accuracy.
- Outreach copy remains draft-only and human-reviewed.
- Use `channel-portfolio-selector` for channel allocation and `ai-pricing` for packaging.
