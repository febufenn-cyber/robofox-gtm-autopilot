#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

# Project-scoped MCP definitions must exist and remain read-only endpoints.
mcp_path = ROOT / ".mcp.json"
if not mcp_path.exists():
    errors.append("missing .mcp.json")
else:
    import json
    try:
        mcp = json.loads(mcp_path.read_text())
        servers = mcp.get("mcpServers", {})
        expected = {
            "hubspot": "https://mcp.hubspot.com/anthropic",
            "meta-ads": "https://mcp.facebook.com/ads",
        }
        for name, url in expected.items():
            entry = servers.get(name, {})
            if entry.get("type") != "http" or entry.get("url") != url:
                errors.append(f"invalid MCP definition: {name}")
    except Exception as exc:
        errors.append(f"invalid .mcp.json: {exc}")

required = [
    ROOT / '.claude/skills',
    ROOT / 'context/products',
    ROOT / 'plans',
    ROOT / 'reviews',
    ROOT / 'vendor/agent-gtm-skills',
    ROOT / 'README.md',
]
for path in required:
    if not path.exists():
        errors.append(f'missing: {path.relative_to(ROOT)}')

for skill_file in sorted((ROOT / '.claude/skills').glob('*/SKILL.md')):
    lines = skill_file.read_text().splitlines()
    if len(lines) >= 500:
        errors.append(f'{skill_file.relative_to(ROOT)} has {len(lines)} lines; must be <500')
    text = '\n'.join(lines)
    if not text.startswith('---\nname:') or '\ndescription:' not in text.split('---', 2)[1]:
        errors.append(f'bad minimal frontmatter: {skill_file.relative_to(ROOT)}')
    if 'Do NOT use' not in text.split('---', 2)[1]:
        errors.append(f'missing negative trigger boundary: {skill_file.relative_to(ROOT)}')

selector = (ROOT / '.claude/skills/channel-portfolio-selector/SKILL.md').read_text()
review = (ROOT / '.claude/skills/kill-criteria-review/SKILL.md').read_text()
if 'build a channel plan for my voice agent product' not in selector:
    errors.append('selector natural-language trigger missing')
if 'run my weekly GTM kill review' not in review:
    errors.append('review natural-language trigger missing')

product = (ROOT / 'context/products/voice-agents.md').read_text().splitlines()
expected_fields = [
    'product', 'geography', 'pricing_hypothesis', 'ACV_usd', 'motion', 'stage',
    'team_size', 'budget_monthly_usd', 'existing_audience',
    'channels_already_available', 'failed_channels'
]
actual_fields = [line.split(':', 1)[0] for line in product if line.strip()]
if actual_fields != expected_fields:
    errors.append(f'voice-agents fields differ: {actual_fields}')

template = (ROOT / 'context/products/_template.md').read_text().splitlines()
template_fields = [line.split(':', 1)[0] for line in template if line.strip()]
if template_fields != expected_fields:
    errors.append('template fields differ')

plan = (ROOT / 'plans/voice-agents-portfolio-2026-07-12.md').read_text()
checks = {
    'benchmark citation': 'benchmarks-2026.md',
    'budget total': '**100%**',
    'paid zero': '**Ad spend: 0%.**',
    'founder-led rank 1': '### 1. Founder-led local sales',
    'kill criteria': '**Kill criterion:**',
    'week 13': '| 13 |',
    'override n>=30': 'at least 30 relevant data points',
}
for label, needle in checks.items():
    if needle not in plan:
        errors.append(f'plan missing {label}')

ranked_section = plan.split('## Ranked portfolio', 1)[1].split('## Monthly budget split', 1)[0]
if re.search(r'^### \d+\..*(Meta|LinkedIn ads|paid newsletter)', ranked_section, flags=re.M | re.I):
    errors.append('paid channel ranked despite <$500 budget gate')

budget_values = [35, 20, 20, 15, 10]
if sum(budget_values) != 100:
    errors.append('budget does not total 100')

if errors:
    print('VERIFY: FAIL')
    for error in errors:
        print(f'- {error}')
    sys.exit(1)

print('VERIFY: PASS')
for skill_file in sorted((ROOT / '.claude/skills').glob('*/SKILL.md')):
    print(f'- {skill_file.relative_to(ROOT)}: {len(skill_file.read_text().splitlines())} lines')
print('- natural trigger: build a channel plan for my voice agent product')
print('- natural trigger: run my weekly GTM kill review')
print('- dry-run plan obeys <$500 owned-channel gate and cites benchmarks')
