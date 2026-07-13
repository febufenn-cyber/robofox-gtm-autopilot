"""Strict validation for Phase 3 experiment records."""
from __future__ import annotations
import math, re
from datetime import datetime
from typing import Any
from robofox_truth.validation import TruthStoreError, canonical_json, parse_datetime, record_hash, require_product
from .constants import CHANGE_DIMENSIONS, CRITERION_STATUSES, HASH_RE, ID_PATTERNS, OPERATORS, OUTCOME_TO_STATE, SENSITIVITY, STATES

DEFINITION_KEYS={"version","id","product","decision_id","decision_record_hash","candidate_id","candidate_hash","snapshot_hash","decision_status","hypothesis","target_segment","audience_key","change_dimensions","primary_metric","secondary_metrics","minimum_execution","maximum_exposure","planned_start","planned_end","success_criteria","kill_criteria","hard_stop_conditions","owner","collision_waiver","sensitivity","registered_at"}
TRANSITION_KEYS={"version","id","experiment_id","from_state","to_state","reason","actor","occurred_at"}
EXECUTION_KEYS={"version","id","experiment_id","units","cash_spent_usd","founder_hours","source_ids","notes","occurred_at"}
OBSERVATION_KEYS={"version","id","experiment_id","metric","value","unit","sample_size","denominator","source_ids","observed_at"}
OUTCOME_KEYS={"version","id","experiment_id","outcome","conclusion","learning","belief_updates","evidence_observation_ids","criterion_results","triggered_hard_stop","next_action","transition"}
CRITERION_KEYS={"metric","operator","threshold","unit","minimum_sample_size"}

def _exact(value:dict[str,Any], keys:set[str], field:str)->None:
    if not isinstance(value,dict): raise TruthStoreError(f"{field} must be an object")
    unknown=set(value)-keys; missing=keys-set(value)
    if unknown or missing: raise TruthStoreError(f"invalid {field} fields; missing={sorted(missing)} unknown={sorted(unknown)}")
def _string(value:Any, field:str, minimum:int=1, maximum:int=2000)->str:
    if not isinstance(value,str) or not minimum<=len(value.strip())<=maximum: raise TruthStoreError(f"{field} must be a non-empty string")
    return value
def _id(value:Any, kind:str)->str:
    if not isinstance(value,str) or not ID_PATTERNS[kind].fullmatch(value): raise TruthStoreError(f"invalid {kind} id")
    return value
def _hash(value:Any, field:str)->str:
    if not isinstance(value,str) or not HASH_RE.fullmatch(value): raise TruthStoreError(f"{field} must be a canonical sha256 hash")
    return value
def _finite(value:Any, field:str, minimum:float=0)->float:
    if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(float(value)) or float(value)<minimum:
        raise TruthStoreError(f"{field} must be a finite number >= {minimum}")
    return float(value)
def _integer(value:Any, field:str, minimum:int=0)->int:
    if not isinstance(value,int) or isinstance(value,bool) or value<minimum: raise TruthStoreError(f"{field} must be an integer >= {minimum}")
    return value
def _strings(value:Any, field:str, minimum:int=0)->list[str]:
    if not isinstance(value,list) or len(value)<minimum or any(not isinstance(x,str) or not x.strip() for x in value):
        raise TruthStoreError(f"{field} must be a string list")
    if len(value)!=len(set(value)): raise TruthStoreError(f"{field} contains duplicates")
    return list(value)
def _date(value:Any, field:str)->str:
    parsed=parse_datetime(value,field); assert parsed is not None; return parsed
def _criteria(items:Any, field:str)->list[dict[str,Any]]:
    if not isinstance(items,list) or not items: raise TruthStoreError(f"{field} must contain at least one criterion")
    result=[]; seen=set()
    for index,item in enumerate(items):
        _exact(item,CRITERION_KEYS,f"{field}[{index}]")
        metric=_string(item["metric"],f"{field}[{index}].metric",2,80)
        operator=item["operator"]
        if operator not in OPERATORS: raise TruthStoreError(f"{field}[{index}].operator is invalid")
        unit=_string(item["unit"],f"{field}[{index}].unit",1,40)
        threshold=_finite(item["threshold"],f"{field}[{index}].threshold",-1e308)
        sample=_integer(item["minimum_sample_size"],f"{field}[{index}].minimum_sample_size",0)
        key=(metric,operator,threshold,unit,sample)
        if key in seen: raise TruthStoreError(f"{field} contains duplicate criteria")
        seen.add(key); result.append({"metric":metric,"operator":operator,"threshold":threshold,"unit":unit,"minimum_sample_size":sample})
    return result

def validate_definition(raw:dict[str,Any])->dict[str,Any]:
    _exact(raw,DEFINITION_KEYS,"experiment definition")
    if raw["version"]!=1: raise TruthStoreError("unsupported experiment definition version")
    if raw["decision_status"]!="CHOSEN": raise TruthStoreError("experiment requires a CHOSEN Phase 2 decision")
    start=_date(raw["planned_start"],"planned_start"); end=_date(raw["planned_end"],"planned_end")
    if datetime.fromisoformat(end)<datetime.fromisoformat(start): raise TruthStoreError("planned_end cannot precede planned_start")
    audience=_string(raw["audience_key"],"audience_key",3,120)
    if "@" in audience or re.search(r"\b[6-9]\d{9}\b",audience): raise TruthStoreError("audience_key must be pseudonymous and contain no contact data")
    dimensions=_strings(raw["change_dimensions"],"change_dimensions",1)
    if not set(dimensions)<=CHANGE_DIMENSIONS: raise TruthStoreError("change_dimensions contains an unsupported dimension")
    secondary=_strings(raw["secondary_metrics"],"secondary_metrics")
    primary=_string(raw["primary_metric"],"primary_metric",2,80)
    if primary in secondary: raise TruthStoreError("primary_metric cannot also be secondary")
    minimum=raw["minimum_execution"]
    _exact(minimum,{"unit","target"},"minimum_execution")
    minimum={"unit":_string(minimum["unit"],"minimum_execution.unit",1,40),"target":_integer(minimum["target"],"minimum_execution.target",1)}
    exposure=raw["maximum_exposure"]
    _exact(exposure,{"cash_usd","founder_hours","days_to_signal"},"maximum_exposure")
    exposure={"cash_usd":_finite(exposure["cash_usd"],"maximum_exposure.cash_usd"),"founder_hours":_finite(exposure["founder_hours"],"maximum_exposure.founder_hours"),"days_to_signal":_integer(exposure["days_to_signal"],"maximum_exposure.days_to_signal",1)}
    waiver=raw["collision_waiver"]
    if waiver is not None:
        _exact(waiver,{"conflicting_experiment_ids","reason","isolation_plan"},"collision_waiver")
        waiver={"conflicting_experiment_ids":sorted(_strings(waiver["conflicting_experiment_ids"],"collision_waiver.conflicting_experiment_ids",1)),"reason":_string(waiver["reason"],"collision_waiver.reason",10),"isolation_plan":_string(waiver["isolation_plan"],"collision_waiver.isolation_plan",10)}
    result={
      "version":1,"id":_id(raw["id"],"experiment"),"product":require_product(raw["product"]),
      "decision_id":_string(raw["decision_id"],"decision_id",4,100),"decision_record_hash":_hash(raw["decision_record_hash"],"decision_record_hash"),
      "candidate_id":_string(raw["candidate_id"],"candidate_id",4,100),"candidate_hash":_hash(raw["candidate_hash"],"candidate_hash"),"snapshot_hash":_hash(raw["snapshot_hash"],"snapshot_hash"),"decision_status":"CHOSEN",
      "hypothesis":_string(raw["hypothesis"],"hypothesis",10),"target_segment":_string(raw["target_segment"],"target_segment",3,200),"audience_key":audience,
      "change_dimensions":sorted(dimensions),"primary_metric":primary,"secondary_metrics":sorted(secondary),"minimum_execution":minimum,"maximum_exposure":exposure,
      "planned_start":start,"planned_end":end,"success_criteria":_criteria(raw["success_criteria"],"success_criteria"),"kill_criteria":_criteria(raw["kill_criteria"],"kill_criteria"),
      "hard_stop_conditions":_strings(raw["hard_stop_conditions"],"hard_stop_conditions",1),"owner":_string(raw["owner"],"owner",2,120),"collision_waiver":waiver,
      "sensitivity":raw["sensitivity"],"registered_at":_date(raw["registered_at"],"registered_at")}
    if result["sensitivity"] not in SENSITIVITY: raise TruthStoreError("experiment sensitivity must be INTERNAL or CONFIDENTIAL")
    declared={primary,*secondary}
    criterion_metrics={x["metric"] for x in result["success_criteria"]+result["kill_criteria"]}
    if not criterion_metrics<=declared: raise TruthStoreError("every criterion metric must be declared as primary or secondary")
    return result

def validate_transition(raw:dict[str,Any])->dict[str,Any]:
    _exact(raw,TRANSITION_KEYS,"experiment transition")
    if raw["version"]!=1: raise TruthStoreError("unsupported transition version")
    if raw["from_state"] not in STATES or raw["to_state"] not in STATES: raise TruthStoreError("transition state is invalid")
    return {"version":1,"id":_id(raw["id"],"transition"),"experiment_id":_id(raw["experiment_id"],"experiment"),"from_state":raw["from_state"],"to_state":raw["to_state"],"reason":_string(raw["reason"],"reason",5),"actor":_string(raw["actor"],"actor",2,120),"occurred_at":_date(raw["occurred_at"],"occurred_at")}

def validate_execution(raw:dict[str,Any])->dict[str,Any]:
    _exact(raw,EXECUTION_KEYS,"experiment execution")
    if raw["version"]!=1: raise TruthStoreError("unsupported execution version")
    units=_integer(raw["units"],"units",0); cash=_finite(raw["cash_spent_usd"],"cash_spent_usd"); hours=_finite(raw["founder_hours"],"founder_hours")
    if units==0 and cash==0 and hours==0: raise TruthStoreError("execution event must record at least one non-zero exposure")
    return {"version":1,"id":_id(raw["id"],"execution"),"experiment_id":_id(raw["experiment_id"],"experiment"),"units":units,"cash_spent_usd":cash,"founder_hours":hours,"source_ids":sorted(_strings(raw["source_ids"],"source_ids")),"notes":_string(raw["notes"],"notes",1) if raw["notes"] is not None else None,"occurred_at":_date(raw["occurred_at"],"occurred_at")}

def validate_observation(raw:dict[str,Any])->dict[str,Any]:
    _exact(raw,OBSERVATION_KEYS,"experiment observation")
    if raw["version"]!=1: raise TruthStoreError("unsupported observation version")
    denominator=raw["denominator"]
    if denominator is not None: denominator=_finite(denominator,"denominator")
    return {"version":1,"id":_id(raw["id"],"observation"),"experiment_id":_id(raw["experiment_id"],"experiment"),"metric":_string(raw["metric"],"metric",2,80),"value":_finite(raw["value"],"value",-1e308),"unit":_string(raw["unit"],"unit",1,40),"sample_size":_integer(raw["sample_size"],"sample_size",0),"denominator":denominator,"source_ids":sorted(_strings(raw["source_ids"],"source_ids")),"observed_at":_date(raw["observed_at"],"observed_at")}

def validate_outcome(raw:dict[str,Any])->dict[str,Any]:
    _exact(raw,OUTCOME_KEYS,"experiment outcome")
    if raw["version"]!=1 or raw["outcome"] not in OUTCOME_TO_STATE: raise TruthStoreError("experiment outcome is invalid")
    transition=validate_transition(raw["transition"])
    if transition["to_state"]!=OUTCOME_TO_STATE[raw["outcome"]]: raise TruthStoreError("outcome terminal state does not match outcome type")
    results=raw["criterion_results"]
    if not isinstance(results,dict) or set(results)!={"success","kill"}: raise TruthStoreError("criterion_results must contain success and kill")
    for group in ("success","kill"):
        if not isinstance(results[group],list): raise TruthStoreError("criterion result groups must be lists")
        for item in results[group]:
            expected={"metric","operator","threshold","unit","minimum_sample_size","observation_id","observed_value","sample_size","status"}
            _exact(item,expected,"criterion result")
            if item["status"] not in CRITERION_STATUSES: raise TruthStoreError("criterion result status is invalid")
    updates=raw["belief_updates"]
    if not isinstance(updates,list): raise TruthStoreError("belief_updates must be a list")
    for item in updates:
        _exact(item,{"belief","previous_state","new_state","confidence","evidence_ids"},"belief update")
        _string(item["belief"],"belief",5); _string(item["previous_state"],"previous_state"); _string(item["new_state"],"new_state");
        if item["confidence"] not in {"LOW","MEDIUM","HIGH"}: raise TruthStoreError("belief update confidence is invalid")
        _strings(item["evidence_ids"],"belief_update.evidence_ids")
    hard=raw["triggered_hard_stop"]
    if hard is not None: hard=_string(hard,"triggered_hard_stop",3)
    return {"version":1,"id":_id(raw["id"],"outcome"),"experiment_id":_id(raw["experiment_id"],"experiment"),"outcome":raw["outcome"],"conclusion":_string(raw["conclusion"],"conclusion",10),"learning":_string(raw["learning"],"learning",10),"belief_updates":updates,"evidence_observation_ids":sorted(_strings(raw["evidence_observation_ids"],"evidence_observation_ids")),"criterion_results":results,"triggered_hard_stop":hard,"next_action":_string(raw["next_action"],"next_action",5),"transition":transition}

__all__=["TruthStoreError","canonical_json","record_hash","validate_definition","validate_transition","validate_execution","validate_observation","validate_outcome"]
