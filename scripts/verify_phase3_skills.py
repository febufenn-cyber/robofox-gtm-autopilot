#!/usr/bin/env python3
"""Verify the installed Phase 3 Claude skills."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAMES=('experiment-designer','experiment-controller','experiment-reviewer')
def verify(root:Path=ROOT)->list[str]:
    errors=[]
    for name in NAMES:
        path=root/'.claude/skills'/name/'SKILL.md'
        if not path.is_file(): errors.append(f'missing Phase 3 skill: {name}'); continue
        text=path.read_text(encoding='utf-8'); lines=text.splitlines()
        if len(lines)>=500: errors.append(f'{name} skill must stay below 500 lines')
        if not text.startswith('---\nname:') or '\ndescription:' not in text.split('---',2)[1]: errors.append(f'bad skill frontmatter: {name}')
        if 'Do NOT use' not in text.split('---',2)[1]: errors.append(f'missing negative boundary: {name}')
    return errors
def main()->int:
    errors=verify()
    if errors:
        print('PHASE3 SKILLS: FAIL'); [print(f'- {x}') for x in errors]; return 1
    print('PHASE3 SKILLS: PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
