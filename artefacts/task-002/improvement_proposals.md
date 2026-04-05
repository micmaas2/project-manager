# Improvement Proposals — task-002

## Proposal 1: Add shellcheck to prerequisites in MVP template (when used in acceptance criteria)

**Source**: task-002 Reviewer found shellcheck not installed; acceptance criterion "passes shellcheck" could not be verified automatically.

**Change needed**: In `manager.yaml` planning instructions — when generating an MVP template for a bash script task, if the acceptance criteria include "passes shellcheck", automatically add `shellcheck` to `mvp_template.prerequisites`. PM preflight will then catch it before Builder runs.

**Impact**: low — single addition to manager.yaml planning heuristics.
**Human gate required**: Yes — affects manager.yaml behaviour.

---

## Proposal 2: Builder self-review for no-op pipeline stages

**Source**: task-002 audit-summary.sh contained a no-op `sed 's/^//'` that slipped through the build step.

**Change needed**: In `builder.yaml` — add a self-check instruction: "Before writing the final script, trace each pipeline stage. If a stage has no observable effect on stdin/stdout (e.g., `sed 's/^//'`, `cat -`, `tr '' ''`), remove it."

**Impact**: minimal — single instruction addition to builder.yaml.
**Human gate required**: Yes — affects builder.yaml behaviour.
