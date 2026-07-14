"""Policy-bound service functions for simulator execution."""
from __future__ import annotations
import json, sqlite3
from pathlib import Path
from typing import Any
from .approval import consume, validate_approval, workspace_id
from .store import execute_simulated, install_schema, rollback_simulated
from .validation import ExecutionError

def validate_private_state(workspace:Path,state_path:Path)->dict[str,Any]:
    workspace=workspace.resolve(); state_path=state_path.resolve()
    try: state_path.relative_to(workspace)
    except ValueError as exc: raise ExecutionError('system-state file must be inside private workspace') from exc
    state=json.loads(state_path.read_text())
    if state.get('workspace_id')!=workspace_id(workspace): raise ExecutionError('system-state workspace_id mismatch')
    if state.get('kill_switch') is not False: raise ExecutionError('kill switch blocks simulator execution')
    if state.get('simulation_enabled') is not True: raise ExecutionError('simulation_enabled must be explicitly true')
    if state.get('external_execution') is not False: raise ExecutionError('external_execution must remain false in Phase 4')
    return state

def approved_execute(connection:sqlite3.Connection,workspace:Path,state_path:Path,envelope:dict[str,Any],manifest:dict[str,Any],approval:dict[str,Any],*,now:str)->dict[str,Any]:
    validate_private_state(workspace,state_path); install_schema(connection)
    validate_approval(workspace,'execute_simulated_action',envelope,manifest,approval,now=now)
    with connection:
        result=execute_simulated(connection,envelope,completed_at=now,commit=False)
        consume(connection,manifest,approval,envelope,now)
    return result

def approved_rollback(connection:sqlite3.Connection,workspace:Path,state_path:Path,record:dict[str,Any],manifest:dict[str,Any],approval:dict[str,Any],*,now:str,fail:bool=False)->dict[str,Any]:
    validate_private_state(workspace,state_path); install_schema(connection)
    validate_approval(workspace,'rollback_simulated_action',record,manifest,approval,now=now)
    with connection:
        result=rollback_simulated(connection,record,fail=fail,commit=False)
        consume(connection,manifest,approval,record,now)
    return result
