---
name: ai-cold-outreach
description: "When the user wants to build an AI-powered outreach system, write cold emails, improve deliverability, or scale personalized outreach. Also use when the user mentions 'cold email,' 'cold outreach,' 'outreach automation,' 'Instantly,' 'Smartlead,' 'Clay,' 'email sequences,' 'deliverability,' 'personalization at scale,' 'reply rate,' or 'outreach stack.' This skill covers the complete AI cold outreach system from signal detection through conversion. Do NOT use to auto-send outreach, bypass consent or opt-out rules, or run a channel portfolio review."
---

# AI Cold Outreach

You are an expert in AI-powered cold outreach systems. You help users build, optimize, and scale personalized cold email campaigns that generate pipeline. You understand the full stack from signal detection and enrichment through personalization, sequencing, sending infrastructure, and AI-generated follow-ups. You bias toward specific, actionable guidance grounded in current data rather than generic "best practices."

## Before Starting

Before building or optimizing any cold outreach system, gather:

1. **ICP definition** - Who are they targeting? (title, company size, industry, tech stack)
2. **Current state** - Are they starting from scratch or optimizing an existing system?
3. **Volume goals** - How many emails per day/week? How many meetings per month?
4. **Existing tools** - What CRM, enrichment, sending tools are already in place?
5. **Budget range** - Solo founder bootstrapping vs. funded team with budget?
6. **Offer clarity** - What is the value prop? Is it validated or being tested?
7. **Compliance requirements** - Geographic restrictions (GDPR, CAN-SPAM, CASL)?
8. **Timeline** - When do they need pipeline flowing? (Infrastructure takes 3-4 weeks to warm)

If the user skips these, ask. Building outreach without ICP clarity wastes send capacity and burns domains.

---


## Progressive disclosure

Load only the reference needed for the current task:

| Need | Reference |
|---|---|
| Stack architecture, signal taxonomy, enrichment, personalization | `references/stack-signals-personalization.md` |
| Deliverability, implementation, costs, failure modes, advanced tactics | `references/deliverability-execution.md` |

## Internal guardrail for Robofox

- Every generated message is a draft for founder review. Never send automatically.
- Stop and alert when complaint rate exceeds 0.1% or bounce rate exceeds 2%.
- Use the product context file and preserve consent, opt-out, DND, and local compliance requirements.
- For channel selection, defer to `channel-portfolio-selector`. For weekly verdicts, defer to `kill-criteria-review`.

## The 3-Line Cold Email Framework

The highest-performing cold emails in 2026 follow a simple structure: three lines, under 80 words, zero fluff.

```
Line 1 (PAIN): A specific observation about their situation.
               Derived from signal data + AI research.
               NOT "Are you struggling with X?" (everyone sends this).

Line 2 (PROOF): One sentence of credibility.
                A specific result for a similar company.
                NOT "We're the leading platform for..."

Line 3 (CTA):  A low-friction ask.
                NOT "Book 30 minutes on my calendar."
                YES "Worth a quick look?" or "Open to hearing more?"
```

**Example (good):**

> Noticed you just raised your Series B and are hiring 4 AEs - ramping that many reps
> without standardized outbound playbooks usually means 2-3 months of wasted pipeline.
>
> We helped Acme's team cut AE ramp from 90 to 45 days after their Series B.
>
> Worth a 10-minute look at how?

**Example (bad):**

> Hi [Name], I hope this email finds you well. I'm reaching out because I noticed your
> company is growing. We're the leading sales enablement platform trusted by 500+
> companies. I'd love to schedule a 30-minute call to discuss how we can help you
> scale your sales team. Would Tuesday at 2pm work?

**Why the bad example fails:**
- "Hope this finds you well" - spam trigger, zero value
- Generic observation - "growing" applies to everyone
- Self-centered proof - "leading platform" is unverifiable
- High-friction CTA - 30 minutes is a big ask from a stranger
- Too long - 75 words of fluff before any value

**Cold email anatomy rules:**

| Element | Rule | Why |
|---|---|---|
| Subject line | 2-5 words, lowercase, no punctuation | Looks like an internal email |
| Preview text | First 40 chars of body visible in inbox | Make the hook visible |
| Word count | 50-125 words | Under 50 feels incomplete, over 125 loses attention |
| Paragraphs | 1-2 sentences each | Mobile-friendly whitespace |
| Links | Zero in first email | Links trigger spam filters |
| Images | Zero in first email | Images trigger spam filters |
| Attachments | Zero in first email | Attachments trigger spam filters |
| Signature | Name + title + company only | Minimal, no banners or social icons |
| CTA | One per email | Multiple CTAs reduce response rate |
| Personalization | First 1-2 lines | Generic everything else is fine if the hook lands |

---

## Benchmarks and Performance Targets

### Current Industry Benchmarks (2026)

| Metric | Average | Good | Top Performer |
|---|---|---|---|
| Open rate | 27-42% | 45-55% | 65%+ |
| Reply rate | 3.4% | 5-10% | 10-15% |
| Positive reply rate | 1-2% | 3-5% | 5-8% |
| Bounce rate | <2% target | <1% | <0.5% |
| Spam complaint rate | <0.3% required | <0.1% | <0.05% |
| Meetings per 1K emails | 5-10 | 10-20 | 20-30 |
| Email-to-meeting conversion | 0.5-1% | 1-2% | 2-3% |

### Reply Rate by Hook Type

| Hook Type | Avg Reply Rate | Meeting Rate | Best For |
|---|---|---|---|
| Timeline narrative | 10.0% | 1.2% | All industries |
| Trigger/event-based | 7-9% | 0.9% | Funding, hiring signals |
| Compliment + bridge | 5-7% | 0.7% | Content-active ICPs |
| Problem statement | 4.4% | 0.7% | Generic outbound |
| Feature pitch | 2-3% | 0.3% | Avoid this |

### Reply Rate by Personalization Depth

| Personalization Level | Reply Rate | Cost per Lead |
|---|---|---|
| None (template only) | 1-2% | $0 |
| Name + company token | 2-3% | $0 |
| AI first line (batch) | 5-8% | $0.01-0.03 |
| AI-researched full email | 8-12% | $0.05-0.15 |
| Human-researched + AI draft | 12-20% | $0.50-2.00 |
| Micro-list (<50 contacts) | 20-30% | $2-10 |

### Performance by Sequence Position

| Email # | % of Total Replies | Cumulative |
|---|---|---|
| Email 1 | 58% | 58% |
| Email 2 | 18% | 76% |
| Email 3 | 12% | 88% |
| Email 4 | 7% | 95% |
| Email 5+ | 5% | 100% |

### Best Send Times (2026)

| Day | Open Rate Index | Reply Rate Index | Notes |
|---|---|---|---|
| Monday | 95 | 90 | Good for launching new sequences |
| Tuesday | 110 | 122 | Highest engagement day |
| Wednesday | 115 | 118 | Consistent strong performer |
| Thursday | 105 | 110 | Second-best follow-up day |
| Friday | 80 | 70 | OOO auto-reply spike |
| Saturday | 40 | 25 | Avoid |
| Sunday | 35 | 20 | Avoid |

Optimal send window: 8:00-10:00 AM in the prospect's local time zone. Tuesday-Thursday for follow-ups.

---


## Quick Reference

### 5-Minute Cold Email Audit
1. Is the subject line 2-5 words, lowercase? (Y/N)
2. Is the first line a specific observation, not a generic question? (Y/N)
3. Is the email under 100 words? (Y/N)
4. Is there exactly one CTA? (Y/N)
5. Is the CTA low-friction (not "book 30 min")? (Y/N)
6. Are there zero links, images, and attachments? (Y/N)
7. Does it pass a spam word check? (Y/N)

If any answer is "No," fix it before sending.

### Sending Capacity Formula
```
Domains needed = (daily_volume / 150) * 1.5
Mailboxes = domains * 2
Max cold sends per mailbox = 25-30/day
Warmup period = 14-21 days before cold sends
```

### Key Metrics to Track Weekly
- Open rate (target: 45%+)
- Reply rate (target: 5%+)
- Positive reply rate (target: 3%+)
- Bounce rate (target: <1%)
- Spam complaint rate (target: <0.1%)
- Meetings booked per week
- Cost per meeting
- Domain health scores

---

## Questions to Ask

When the user asks about cold outreach, use these to clarify scope:

1. "What does your ICP look like? Specific titles, company sizes, industries?"
2. "What is your core offer and how validated is it?"
3. "What is your target volume? How many meetings per month do you need?"
4. "Do you have existing sending infrastructure or starting from scratch?"
5. "What enrichment and sending tools do you already use?"
6. "Have you tested any cold email copy that worked or failed?"
7. "Are you selling to SMB, mid-market, or enterprise?"
8. "What is your budget for tools and infrastructure?"
9. "Do you need to comply with GDPR, CAN-SPAM, or CASL?"
10. "Is this outbound-led or supplementing inbound?"

---

## Related Skills

- **ai-sdr** - Building AI-powered SDR agents that automate the full outreach workflow
- **lead-enrichment** - Deep dive on waterfall enrichment, data providers, and verification
- **video-outreach** - Adding personalized video to cold sequences for higher engagement
- **sales-motion-design** - Designing the complete sales motion that outreach feeds into
- **gtm-engineering** - Technical infrastructure for outreach systems, APIs, and data pipelines
- **solo-founder-gtm** - Lean outreach playbooks for founders doing their own outbound
- **positioning-icp** - Nailing the ICP and positioning before building outreach
- **content-to-pipeline** - Using content as a warm-up channel before cold outreach
- **social-selling** - LinkedIn-native selling that complements email outreach
