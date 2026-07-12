#!/usr/bin/env python3
from phase0_policy import scan_public_repo

findings = scan_public_repo()
if findings:
    print("PUBLIC REPO SCAN: FAIL")
    for finding in findings:
        print(f"- {finding}")
    raise SystemExit(1)
print("PUBLIC REPO SCAN: PASS")
