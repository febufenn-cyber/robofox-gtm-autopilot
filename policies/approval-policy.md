# Approval Policy

Phase 0 does not enable external execution. This policy defines the contract future execution must satisfy.

An approval is valid only when it binds to:

- one action identifier and action type
- an exact normalized manifest hash
- exact scope and maximum affected records
- exact recipient or target when applicable
- approving actor
- approval timestamp and expiry
- experiment or decision identifier

Approval becomes invalid when content, recipient, attachment, price, claim, budget, campaign, or scope changes. Approval cannot be reused after execution and cannot be replayed after expiry.

Broad phrases such as “send it,” “do all,” or “go ahead” are not sufficient to authorize an unbounded action. Missing or ambiguous approval fails closed.
