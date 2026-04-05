# Lessons Learned

Post-session retrospective notes. Updated after each agent run or user correction.

| Date | Agent | Lesson | Applied To |
|------|-------|--------|------------|
| 2026-04-05 | Builder | **Verify tool availability before scripting**: `jq` was not installed at build time. Scripts with external dependencies should check for the tool and emit a clear error — and the MVP template should list runtime prerequisites under `tests_required` or a new `prerequisites` field. | All future Builder tasks |
| 2026-04-05 | ProjectManager | **Execute agents sequentially with queue.json as shared state**: The queue.json file is the effective handoff contract between agents — each agent reads status and assigned_to to know what to do. Keeping it updated after every step prevents context drift in multi-step pipelines. | All future pipelines |
| 2026-04-05 | Tester | **Test with fixtures, not just live data**: Running tests against the real queue.json ties test results to live system state. Always test with at least one controlled fixture (empty queue, seeded queue) to make acceptance criteria provable independently of current system state. | All future Tester runs |
| 2026-04-05 | Builder/Reviewer | **List all acceptance-criteria tools in prerequisites**: If an acceptance criterion says "passes shellcheck", then shellcheck must appear in `mvp_template.prerequisites`. The preflight step catches missing tools before Builder runs — but only for tools that are declared. Undeclared tools fail silently during review. | All future tasks with static-analysis criteria |
| 2026-04-05 | Builder | **Avoid no-op pipeline stages**: A `sed 's/^//'` (replace start-of-line with nothing) has no effect and adds a pointless pipeline stage. Reviewer caught it but it still shipped. Builder should not emit commands that do nothing — if unsure, test the pipeline without the stage first. | All future Builder script tasks |

