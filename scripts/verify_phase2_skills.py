#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SKILLS={
 'kasparov-decision-workflow':['frozen','candidate-move-generator','opponent-model','decision-arbiter'],
 'position-evaluator':['snapshot','unknown','conflict'],
 'candidate-move-generator':['do not include ranking scores','distinct','kill criteria'],
 'opponent-model':['one candidate','blind_review','untrusted'],
 'prophylaxis-review':['verification','residual risk','generic'],
 'decision-arbiter':['ARBITER','deterministic','verify_decision_record.py'],
}
def verify(root:Path=ROOT)->list[str]:
    errors=[]
    for name,needles in SKILLS.items():
        path=root/'.claude/skills'/name/'SKILL.md'
        if not path.is_file(): errors.append(f'missing Phase 2 skill: {name}'); continue
        text=path.read_text(encoding='utf-8')
        if not text.startswith('---\nname:') or text.count('---')<2: errors.append(f'bad skill frontmatter: {name}'); continue
        front=text.split('---',2)[1]
        if 'description:' not in front or 'Do NOT use' not in front: errors.append(f'missing negative trigger boundary: {name}')
        lower=text.lower()
        for needle in needles:
            if needle.lower() not in lower: errors.append(f'{name} missing boundary: {needle}')
    for rel in ('scripts/prepare_decision_pack.py','scripts/verify_decision_record.py','schemas/score-assessment.schema.json'):
        if not (root/rel).is_file(): errors.append(f'missing Phase 2 workflow file: {rel}')
    return errors
if __name__=='__main__':
    errors=verify()
    if errors:
        print('PHASE2 SKILLS: FAIL'); [print(f'- {x}') for x in errors]; raise SystemExit(1)
    print('PHASE2 SKILLS: PASS')
    print('- planner, blind critic, prophylaxis, independent arbiter, replay boundaries')
