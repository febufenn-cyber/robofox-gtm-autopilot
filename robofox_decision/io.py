"""Safe rendering and atomic private-workspace output."""
from __future__ import annotations
import html,json,os,tempfile
from pathlib import Path
from .validation import DecisionError,ROOT

def render_markdown(record):
    chosen=record['chosen_candidate_id'] or 'None'
    lines=[f"# Decision {html.escape(record['decision_id'])}","",f"- **Status:** {record['status']}",f"- **Product:** {html.escape(record['product'])}",f"- **Chosen move:** {html.escape(chosen)}",f"- **Confidence:** {record['confidence']}",f"- **Snapshot:** `{record['snapshot_hash']}`","","## Rationale","",html.escape(record['rationale']),"","## Candidate results","","| Rank | Candidate | Eligible | Positive | Penalty | Final | Blockers |","|---:|---|---|---:|---:|---:|---|"]
    for item in record['candidate_results']:
        blockers=('; '.join(item['blockers']) or '—').replace('|','\\|')
        lines.append(f"| {item['rank'] or '—'} | {html.escape(item['candidate_id'])} | {item['eligible']} | {item['positive_score']} | {item['penalty_score']} | {item['final_score']} | {html.escape(blockers)} |")
    lines += ["","## Evidence that would change the decision",""]+[f"- {html.escape(x)}" for x in record['evidence_that_changes_decision']]+["","_Ordinal scores are comparative controls, not probabilities or revenue forecasts._",""]
    return '\n'.join(lines)

def write_decision(record,workspace:Path):
    root=workspace.resolve()
    try: root.relative_to(ROOT.resolve())
    except ValueError: pass
    else: raise DecisionError('decision workspace cannot be inside the public engine')
    output=root/'decisions'; output.mkdir(parents=True,exist_ok=True)
    stem=f"{record['decision_id']}-{record['created_at'].replace(':','-')}"; paths=(output/f'{stem}.json',output/f'{stem}.md')
    contents=(json.dumps(record,indent=2,ensure_ascii=False)+'\n',render_markdown(record))
    for path,content in zip(paths,contents):
        fd,name=tempfile.mkstemp(prefix=f'.{path.name}.',dir=output); temp=Path(name)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as h: h.write(content); h.flush(); os.fsync(h.fileno())
            os.replace(temp,path)
        finally:
            if temp.exists(): temp.unlink()
    return paths
