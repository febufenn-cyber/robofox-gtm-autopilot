"""Deterministic simulator adapters. No network access is implemented."""
from __future__ import annotations
from typing import Any
from .constants import ADAPTERS
from .validation import ExecutionError

def simulate(envelope:dict[str,Any])->dict[str,Any]:
    adapter=envelope["adapter"]
    if adapter not in ADAPTERS: raise ExecutionError("unknown adapter")
    if envelope["mode"]!="SIMULATOR": raise ExecutionError("live adapter execution is unavailable")
    requested=envelope["payload"].get("simulate_outcome","SUCCESS")
    if requested not in {"SUCCESS","PARTIAL","FAILURE","AMBIGUOUS"}: raise ExecutionError("unsupported simulated outcome")
    total=envelope["batch_size"]
    affected={"SUCCESS":total,"PARTIAL":max(0,total-1),"FAILURE":0,"AMBIGUOUS":0}[requested]
    return {"outcome":requested,"affected_records":affected,"details":{"adapter":adapter,"mode":"SIMULATOR","network_calls":0}}

def simulate_rollback(envelope:dict[str,Any],result:dict[str,Any], *, fail:bool=False)->dict[str,Any]:
    if not ADAPTERS[envelope["adapter"]]["reversible"]: raise ExecutionError("adapter is irreversible")
    return {"outcome":"ROLLBACK_FAILED" if fail else "ROLLED_BACK","details":{"adapter":envelope["adapter"],"network_calls":0,"prior_result":result["id"]}}
