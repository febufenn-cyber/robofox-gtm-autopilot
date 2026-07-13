#!/usr/bin/env python3
"""Verify Phase 3 experiment contracts and policy integration."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    'PHASE3.md', 'policies/experiment-layer-policy.md',
    'decisions/ADR-0014-pre-register-experiments.md',
    'decisions/ADR-0015-derive-experiment-state-from-events.md',
    'decisions/ADR-0016-minimum-execution-and-hard-stops.md',
    'decisions/ADR-0017-detect-experiment-collisions.md',
    'robofox_experiment/migrations/001_experiment_operating_system.sql',
    'schemas/experiment-definition.schema.json',
    'schemas/experiment-transition.schema.json',
    'schemas/experiment-execution.schema.json',
    'schemas/experiment-observation.schema.json',
    'schemas/experiment-outcome.schema.json',
    '.claude/skills/experiment-designer/SKILL.md',
    '.claude/skills/experiment-controller/SKILL.md',
    '.claude/skills/experiment-reviewer/SKILL.md',
]
MUTATIONS = {
    'register_experiment_definition', 'record_experiment_transition',
    'record_experiment_execution', 'record_experiment_observation', 'finalize_experiment',
}

def verify(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (root / relative).is_file(): errors.append(f'missing Phase 3 file: {relative}')
    for path in sorted((root / 'schemas').glob('experiment-*.schema.json')):
        try: data = json.loads(path.read_text(encoding='utf-8'))
        except Exception as exc:
            errors.append(f'invalid JSON schema {path.name}: {exc}'); continue
        if data.get('$schema') != 'https://json-schema.org/draft/2020-12/schema': errors.append(f'wrong schema draft: {path.name}')
        if data.get('type') != 'object' or data.get('additionalProperties') is not False: errors.append(f'experiment schema must be closed object: {path.name}')
        if not data.get('required'): errors.append(f'experiment schema lacks required fields: {path.name}')
    registry = json.loads((root / 'policies/action-registry.yaml').read_text(encoding='utf-8')); actions = registry.get('actions', {})
    if registry.get('version', 0) < 6: errors.append('action registry version must be at least 6')
    for name in MUTATIONS:
        action = actions.get(name)
        if not action: errors.append(f'missing experiment action: {name}'); continue
        if action.get('approval') != 'exact' or action.get('minimum_level') != 'L1': errors.append(f'experiment mutation must be L1 exact approval: {name}')
        if action.get('external') is not False: errors.append(f'experiment record action cannot be external: {name}')
    approval = actions.get('approve_experiment_action', {})
    if approval.get('enabled') is not False or approval.get('approval') != 'forbidden': errors.append('agent experiment approval must be disabled and forbidden')
    execute = actions.get('execute_selected_move', {})
    if execute.get('enabled') is not False or execute.get('approval') != 'forbidden': errors.append('selected-move execution must remain disabled and forbidden')
    policy = (root / 'policies/experiment-layer-policy.md').read_text(encoding='utf-8') if (root / 'policies/experiment-layer-policy.md').exists() else ''
    for phrase in ('Pre-registration', 'Append-only state', 'Minimum execution', 'Collision control', 'External action boundary', 'Fail closed'):
        if phrase not in policy: errors.append(f'experiment policy missing section: {phrase}')
    migration = root / 'robofox_experiment/migrations/001_experiment_operating_system.sql'
    if migration.exists():
        text = migration.read_text(encoding='utf-8')
        for table in ('experiments', 'experiment_transitions', 'experiment_executions', 'experiment_observations', 'experiment_outcomes'):
            if f'CREATE TABLE IF NOT EXISTS {table}' not in text: errors.append(f'migration missing table: {table}')
            if f'{table}_no_update' not in text or f'{table}_no_delete' not in text: errors.append(f'migration missing append-only triggers: {table}')
    return sorted(set(errors))

def main() -> int:
    errors = verify()
    if errors:
        print('PHASE3 CONTRACTS: FAIL')
        for error in errors: print(f'- {error}')
        return 1
    print('PHASE3 CONTRACTS: PASS')
    print('- closed schemas, state policy, exact approvals, collision and exposure contracts')
    return 0

if __name__ == '__main__': raise SystemExit(main())
