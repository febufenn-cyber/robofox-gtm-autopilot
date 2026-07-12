# Incident Response

## Kill switch

Set `ROBOFOX_GTM_KILL_SWITCH=1` or `execution_enabled=false`. All mutating or external actions must stop. Read-only inspection and incident logging may continue.

## Secret or private-data exposure

1. Stop execution and preserve minimal evidence.
2. Revoke and rotate affected credentials immediately.
3. Remove the material from the working tree.
4. Rewrite public history when necessary; deletion in a later commit is insufficient.
5. Audit access, logs, derived files, and downstream systems.
6. Record cause, impact, containment, remediation, and prevention.

## Partial or ambiguous tool result

Do not silently retry a mutating action. Record partial state and require review. Read-only retries must be bounded.
