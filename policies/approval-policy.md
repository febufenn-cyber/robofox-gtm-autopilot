# Approval Policy

External execution remains disabled. Private truth-ledger mutations are the first actions that enforce the exact-approval contract end to end.

An approval is valid only when it binds to:

- one action identifier and registered action type
- an exact canonical manifest hash
- the exact payload hash
- one private workspace identity and ledger path
- one record identifier, or the exact schema version for initialization
- a maximum of one affected record and zero spend
- requesting and approving actor labels
- timezone-aware creation, approval, and expiry timestamps
- a single-use approval identifier

Approval becomes invalid when payload, scope, action, workspace, target record, manifest, or expiry changes. The record insertion and approval consumption commit in one SQLite transaction. Consumed approval and action identifiers cannot be replayed.

The `truth_approval.py approve` command requires a founder-controlled interactive terminal and an exact confirmation phrase. The approval is hash-bound and protected by the private workspace boundary; it is not a cryptographic proof of a human identity. Keep workspace permissions and the approving terminal under founder control.

Broad phrases such as “send it,” “do all,” or “go ahead” never authorize an unbounded action. Missing, ambiguous, expired, mismatched, overlong, or previously consumed approval fails closed. The agent is forbidden from invoking `approve_truth_action`.
