#!/usr/bin/env python3
from phase0_policy import verify

errors = verify()
if errors:
    print("PHASE0 VERIFY: FAIL")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("PHASE0 VERIFY: PASS")
print("- policies and closed schemas present")
print("- L1 advisory state with kill switch active")
print("- default-deny action registry")
print("- external actions and connector writes disabled")
print("- public-repository and upstream-lock checks pass")
