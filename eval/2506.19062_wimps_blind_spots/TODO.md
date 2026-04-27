# TODO

- [ ] Run MadGraph at benchmark points and compare tree-level cross-sections against our Python implementations. This is the external ground truth — our current tests only verify internal consistency (code matches hand calculations of the same formulas). MadGraph computes the same physics from the Lagrangian via an independent code path (diagram generation → amplitude → phase space), so disagreement would catch transcription errors, wrong constants, or convention mismatches that self-tests cannot.
