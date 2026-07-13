#!/usr/bin/env python3
"""Create a private, invalid-until-completed Phase 2 decision work pack."""
from __future__ import annotations
import argparse,json,re,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from robofox_decision import DecisionError,canonical_hash

def atomic(path:Path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshot',required=True);p.add_argument('--workspace',required=True);p.add_argument('--decision-id',required=True);p.add_argument('--question',required=True);p.add_argument('--candidate-count',type=int,default=3);p.add_argument('--max-cash-usd',type=float,required=True);p.add_argument('--max-founder-hours',type=float,required=True);p.add_argument('--max-days-to-signal',type=int,required=True);a=p.parse_args()
    try:
        if not re.fullmatch(r'DEC-[A-Z0-9-]{6,80}',a.decision_id): raise DecisionError('invalid decision ID')
        if not 2<=a.candidate_count<=5: raise DecisionError('candidate count must be 2..5')
        workspace=Path(a.workspace).expanduser().resolve()
        try: workspace.relative_to(ROOT.resolve()); raise DecisionError('decision workspace cannot be inside public engine')
        except ValueError: pass
        snapshot=json.loads(Path(a.snapshot).read_text()); product=snapshot.get('product')
        if not isinstance(product,str): raise DecisionError('snapshot product is missing')
        h=canonical_hash(snapshot); work=workspace/'decisions'/'work'/a.decision_id
        if work.exists(): raise DecisionError('decision work pack already exists')
        now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z'); suffix=a.decision_id.removeprefix('DEC-')
        candidate_ids=[f'MOV-{suffix}-{i:02d}' for i in range(1,a.candidate_count+1)]; review_ids=[f'REV-{suffix}-{i:02d}' for i in range(1,a.candidate_count+1)]; assessment_ids=[f'AST-{suffix}-{i:02d}' for i in range(1,a.candidate_count+1)]
        atomic(work/'frozen-position.json',snapshot)
        atomic(work/'request.json',{'version':1,'decision_id':a.decision_id,'product':product,'snapshot_hash':h,'decision_question':a.question,'constraints':{'max_cash_usd':a.max_cash_usd,'max_founder_hours':a.max_founder_hours,'max_days_to_signal':a.max_days_to_signal},'candidate_ids':candidate_ids,'review_ids':review_ids,'assessment_ids':assessment_ids,'requested_at':now})
        for i,cid in enumerate(candidate_ids):
            atomic(work/'candidates'/f'{cid}.json',{'version':1,'candidate_id':cid,'product':product,'snapshot_hash':h,'title':'','strategic_goal':'','mechanism':'','assumptions':[],'evidence_record_ids':[],'expected_upside':'','success_signal':'','kill_criteria':[],'conversion_plan':'','exposure':{'cash_usd':0,'founder_hours':0,'days_to_signal':1},'trust_risk':1,'created_by_role':'PLANNER','created_at':''})
            atomic(work/'reviews'/f'{review_ids[i]}.json',{'version':1,'review_id':review_ids[i],'candidate_id':cid,'snapshot_hash':h,'reviewer_role':'CRITIC','blind_review':True,'saw_other_critiques':False,'strongest_refutation':'','failure_modes':[],'disconfirming_evidence':[],'threat_level':1,'prophylaxis':[],'residual_risk':1,'reviewed_at':''})
            atomic(work/'assessments'/f'{assessment_ids[i]}.json',{'version':1,'assessment_id':assessment_ids[i],'candidate_id':cid,'snapshot_hash':h,'assessor_role':'ARBITER','saw_all_candidates':True,'saw_critiques':True,'scores':{'constraint_alignment':1,'learning_value':1,'reversibility':1,'execution_feasibility':1,'conversion_readiness':1},'justifications':{'constraint_alignment':'','learning_value':'','reversibility':'','execution_feasibility':'','conversion_readiness':''},'assessed_at':''})
        print(json.dumps({'work_dir':str(work),'snapshot_hash':h,'candidate_ids':candidate_ids,'review_ids':review_ids,'assessment_ids':assessment_ids,'ready':False},indent=2));return 0
    except (DecisionError,OSError,json.JSONDecodeError) as exc: print(f'DECISION PACK: FAIL\n- {exc}',file=sys.stderr);return 1
if __name__=='__main__': raise SystemExit(main())
