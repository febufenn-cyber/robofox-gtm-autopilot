#!/usr/bin/env python3
"""Bind an experiment specification to a chosen Phase 2 decision and candidate."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from robofox_experiment import TruthStoreError, bind_definition
from robofox_truth.approval import load_json_object, write_private_json

def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--decision-record',required=True); p.add_argument('--candidate',required=True); p.add_argument('--spec',required=True); p.add_argument('--output',required=True)
    a=p.parse_args(argv)
    try:
        record=bind_definition(load_json_object(a.decision_record),load_json_object(a.candidate),load_json_object(a.spec))
        path=Path(a.output).expanduser().resolve(); write_private_json(path,record)
        print(json.dumps({'experiment_definition':str(path),'experiment_id':record['id']},indent=2)); return 0
    except (TruthStoreError,OSError) as exc:
        print(f'PREPARE EXPERIMENT: FAIL\n- {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
