# GTM channel benchmarks — 2026 seed set

**As-of date:** 2026-07-12  
**Scope:** Initial decision support for Robofox internal commercialization.  
**Bias rule:** Vendor and aggregator data are directional, not truth. Do not combine incompatible denominators. Do not add a number without a source and a bias label; otherwise mark it `[UNVERIFIED]`.

## Source precedence

1. **Robofox first-party HubSpot/Meta data with at least 30 relevant data points** overrides every industry benchmark below for the matching channel, segment, geography, offer, and metric.
2. First-party data with fewer than 30 relevant data points is a learning signal, not an override.
3. Industry numbers remain comparison context only and must never overrule first-party evidence.

## Seed benchmarks

| Channel / metric | Dated benchmark | Bias flag | Operating interpretation |
|---|---:|---|---|
| Cold email average reply rate | 3.43% — Instantly 2026 | **[VENDOR]** | Directional baseline only. |
| Cold email top-decile reply rate | ≥10.7% — Instantly 2026 | **[VENDOR]** | Do not assume this is attainable for a new list or offer. |
| Replies attributable to email #1 | 58% — Instantly 2026 | **[VENDOR]** | Put the strongest relevance and proof in the first message. |
| AI-written email spam-flag rate | ~8% AI vs ~3% human — DigitalApplied 2026 | **[VENDOR]** | Keep AI as drafting assistance; human-review every message. |
| LinkedIn Ads median CPC | ~$3.94; SaaS ~$8 — Closely 2025 | **[VENDOR]** | Expensive for a sub-$500 monthly budget. |
| LinkedIn Lead Gen Form CVR | 6–10% | **[VENDOR / SOURCE BIAS NOT FULLY SPECIFIED]** | Treat as directional and denominator-sensitive. |
| Meta Advantage+ new-customer CAC | Roughly doubled from $257 to $528, May 2024–May 2025, 55K-campaign study | **[AGGREGATED STUDY; PLATFORM-MEASUREMENT BIAS]** | Do not trust in-platform ROAS as the sole decision signal. |
| SEO position-1 CTR under AI Overviews | ~58% reduction — Ahrefs, Dec 2025 | **[VENDOR STUDY]** | Generic informational content is deprioritized; comparison/entity pages remain candidates. |
| Product Hunt featured outcome | 1–5K visitors; 10–150 signups; ~1–3% conversion | **[AGGREGATED / SELECTION BIAS]** | One-shot channel; evaluate activated users, not upvotes. |
| Niche B2B newsletter economics | CPM $50–100; CPC $1–3 | **[AGGREGATED / PLACEMENT-SPECIFIC]** | Can be cheaper than LinkedIn for the same audience, but is still paid. |
| B2B SaaS blended CAC — SMB | $200–900; payback 8–12 months — Understory 2025 | **[AGGREGATOR]** | Compare only within a similar ACV and sales motion. |
| B2B SaaS blended CAC — mid-market | $1.5–4.5K; payback 14–18 months — Understory 2025 | **[AGGREGATOR]** | Not a target for this product’s current budget/stage. |
| B2B SaaS CPL | SEO $31; email $53; PPC $181 — Understory 2025 | **[AGGREGATOR]** | Channel definitions and attribution vary; use only as directional context. |

## Refresh discipline

At the monthly refresh, record the period, sample size, segment, offer, geography, and denominator for every first-party metric. Once the relevant sample reaches 30, mark the industry row `SUPERSEDED FOR ROBOFOX` and use the first-party number in decisions while retaining the industry figure for historical comparison.
