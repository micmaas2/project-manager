# Build Notes — task-039: Cost-Aware Model Routing Design

## Builder Actions

- Round 1: Inventoried 6 YAML agents, extracted model assignments + prompt sizes, quoted current CLAUDE.md policy
- Round 2: Analysed token_log.jsonl, calculated caching eligibility, assessed Tester downgrade, computed cost deltas
- Wrote design-doc.md and claude-md-additions.md

## Fix Loop (post-review)

All 5 findings ≥80 confidence fixed:

1. **(CQR F2, Reviewer F1, conf 92/97)**: claude-md-additions.md — added `Label all outputs: [Haiku]` to tester.yaml changes (line 35 currently says `[Sonnet]`)
2. **(CQR F4, conf 96)**: claude-md-additions.md — added Sonnet bullet de-list of "testing" + Haiku bullet addition of Tester
3. **(CQR F1, conf 95)**: design-doc.md — added footnoted cost calc with assumed 3,500/1,500 input/output split; corrected figures
4. **(CQR F3, conf 88)**: claude-md-additions.md + design-doc.md — clarified "90% discount on cached input tokens only"
5. **(CQR F5, conf 85)**: design-doc.md — scoped Finding 3 header to "All Analysed Assignments Correct (Architect/Security out of scope)"

## Sub-threshold findings (build_notes only)

- Threshold boundary at exactly 500 tokens (F7, conf 78) — noted as ambiguous; use `>500` for Sonnet lower bound in future
- Tester downgrade monitoring signal not defined (F4, conf 60) — acceptable gap; rollback procedure covers it
