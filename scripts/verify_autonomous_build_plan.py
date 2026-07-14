#!/usr/bin/env python3
"""Verify the remaining-phase autonomous build charter and phase readiness."""
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'roadmap'/'remaining-phases.json';CHARTER=ROOT/'AUTONOMOUS_BUILD_CHARTER.md'

def load_plan()->dict:
 try:value=json.loads(PLAN.read_text(encoding='utf-8'))
 except (OSError,json.JSONDecodeError) as exc:raise ValueError(f'cannot load remaining-phases plan: {exc}') from exc
 if not isinstance(value,dict):raise ValueError('remaining-phases plan must be an object')
 return value

def verify_contract(plan:dict)->list[str]:
 errors=[]
 if plan.get('version')!=1:errors.append('plan version must be 1')
 if plan.get('build_command')!='build':errors.append("build command must be exactly 'build'")
 if plan.get('default_target')!=[4,5,6,7]:errors.append('default target must be phases 4-7')
 if plan.get('advanced_target')!=[8,9]:errors.append('advanced target must be phases 8-9')
 phases=plan.get('phases')
 if not isinstance(phases,list):return errors+['phases must be a list']
 numbers=[item.get('phase') for item in phases if isinstance(item,dict)]
 if numbers!=[4,5,6,7,8,9]:errors.append(f'phases must be ordered 4..9; got {numbers}')
 charter=CHARTER.read_text(encoding='utf-8') if CHARTER.is_file() else ''
 if not charter:errors.append('missing AUTONOMOUS_BUILD_CHARTER.md')
 required={'phase','name','classification','depends_on','objective','deliverables','exit_checks','readiness_files','verification_command','forbidden_actions'}
 for item in phases:
  if not isinstance(item,dict):errors.append('every phase entry must be an object');continue
  phase=item.get('phase');missing=sorted(required-set(item))
  if missing:errors.append(f'phase {phase} missing fields: {missing}')
  expected='core' if phase in {4,5,6,7} else 'advanced'
  if item.get('classification')!=expected:errors.append(f'phase {phase} classification must be {expected}')
  if not isinstance(item.get('objective'),str) or len(item['objective'])<40:errors.append(f'phase {phase} objective is too weak')
  for key,minimum in (('deliverables',4),('exit_checks',5),('forbidden_actions',3)):
   value=item.get(key)
   if not isinstance(value,list) or len(value)<minimum or any(not isinstance(x,str) or not x.strip() for x in value):errors.append(f'phase {phase} {key} must contain at least {minimum} non-empty strings')
  if item.get('depends_on')!=([phase-1] if phase<9 else [7]):errors.append(f"phase {phase} dependency is invalid: {item.get('depends_on')}")
  if item.get('verification_command')!=f'python3 scripts/verify_phase{phase}.py':errors.append(f'phase {phase} verification command is invalid')
  heading=f"## Phase {phase} — {item.get('name')}"
  if heading not in charter:errors.append(f'charter missing heading: {heading}')
 never=set(plan.get('never_autonomous_actions',[]));required_never={'use_real_credentials','contact_customer','spend_money','deploy_production','weaken_constitution'}
 if not required_never.issubset(never):errors.append(f'never-autonomous actions missing: {sorted(required_never-never)}')
 return errors

def verify_readiness(plan:dict,phase_number:int)->list[str]:
 errors=[];phase=next((item for item in plan['phases'] if item['phase']==phase_number),None)
 if phase is None:return [f'phase {phase_number} is not in the plan']
 for relative in phase['readiness_files']:
  if not (ROOT/relative).exists():errors.append(f'phase {phase_number} readiness file missing: {relative}')
 previous=phase_number-1 if phase_number<9 else 7
 if not (ROOT/f'PHASE{previous}.md').is_file():errors.append(f'phase {phase_number} requires PHASE{previous}.md')
 if phase['classification']=='advanced' and not errors:
  report_path=ROOT/phase['readiness_files'][-1]
  try:report=json.loads(report_path.read_text(encoding='utf-8'))
  except (OSError,json.JSONDecodeError) as exc:return [f'phase {phase_number} readiness report invalid: {exc}']
  key=f'phase{phase_number}_ready'
  if report.get(key) is not True:
   reason=report.get(f'phase{phase_number}_reason') or report.get('reason') or 'readiness criteria are not met'
   errors.append(f'ADVANCED_DEFERRED: phase {phase_number} is DEFERRED: {reason}')
 return errors

def main(argv:list[str]|None=None)->int:
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',type=int,choices=range(4,10));parser.add_argument('--readiness',action='store_true');parser.add_argument('--allow-deferred',action='store_true');args=parser.parse_args(argv)
 try:
  plan=load_plan();contract_errors=verify_contract(plan);readiness_errors=[]
  if args.readiness:
   if args.phase is None:readiness_errors.append('--readiness requires --phase')
   else:readiness_errors.extend(verify_readiness(plan,args.phase))
 except ValueError as exc:contract_errors=[str(exc)];readiness_errors=[]
 errors=contract_errors+readiness_errors
 deferred=bool(readiness_errors) and all(error.startswith('ADVANCED_DEFERRED:') for error in readiness_errors) and not contract_errors
 if errors and not (args.allow_deferred and deferred):
  print('AUTONOMOUS BUILD PLAN: FAIL');[print('- '+error) for error in errors];return 1
 if deferred:
  print('AUTONOMOUS BUILD PLAN: DEFERRED');[print('- '+error.removeprefix('ADVANCED_DEFERRED: ')) for error in readiness_errors];print('- core v1 remains complete and valid');return 0
 print('AUTONOMOUS BUILD PLAN: PASS');print('- remaining phases: 4, 5, 6, 7, 8, 9');print('- default build target: phases 4-7');print('- advanced phases 8-9 require readiness reports')
 if args.phase is not None and args.readiness:print(f'- phase {args.phase} readiness: PASS')
 return 0
if __name__=='__main__':raise SystemExit(main())
