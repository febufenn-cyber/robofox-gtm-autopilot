# Supply-Chain Policy

External skills, submodules, actions, packages, benchmarks, and MCP servers are untrusted until reviewed.

- Pin upstream sources to an exact commit or version.
- Never auto-follow a moving default branch.
- Review diffs before updating.
- Restrict the approved source scope.
- Run Phase 0 and skill regression tests after an update.
- Reject unexpected permission, hook, network, or tool requirements.
- Treat benchmark content as evidence, not policy.

The approved upstream lock is stored at `vendor/approved-sources.lock`.
