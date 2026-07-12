# Weekly GTM review schema

Use this structure for `reviews/<ISO-week>.md`:

1. Review period and source plan.
2. Data completeness and sample sizes.
3. Safety alerts: complaint rate, bounce rate, missing consent/opt-out evidence.
4. Channel table: 7-day result, 30-day result, primary KPI, registered threshold, verdict, confidence.
5. One concrete next action per channel.
6. Channels killed this week and what is stopped.
7. First-party metrics that now have at least 30 relevant data points and therefore supersede industry benchmarks.

Allowed verdicts: `KEEP`, `ITERATE`, `KILL`, `INSUFFICIENT DATA`, `PAUSE — SAFETY`.

A verdict must cite either the latest plan’s registered criterion or a named default criterion. Never infer a kill from impressions, clicks, followers, or features shipped when the primary KPI is owner conversations or demos booked.
