# Evidence Policy

Every material statement must use one state:

- `VERIFIED`: direct, current evidence supports it.
- `OBSERVED`: seen in a limited real sample.
- `INFERRED`: a reasoned conclusion from stated evidence.
- `ASSUMED`: required for planning but not yet verified.
- `STALE`: previously supported but outside its validity window.
- `CONFLICTED`: credible sources disagree.
- `UNKNOWN`: no reliable evidence.
- `PROHIBITED`: the information must not be used.

## Required evidence fields

Evidence records include source type, source reference, capture time, valid-as-of time, product, segment, claim, confidence, state, sensitivity, and whether the claim is direct or inferred.

## Precedence

1. Robofox first-party outcomes
2. Direct customer evidence
3. Relevant local-market evidence
4. Comparable India evidence
5. Broad external benchmarks

Missing data is not zero. Partial data must be labelled. A recommendation must lower confidence when it depends materially on assumptions, stale evidence, or conflicted sources.
