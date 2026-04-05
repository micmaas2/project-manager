# Lessons Learned

Post-session retrospective notes. Updated after each agent run or user correction.

| Date | Agent | Lesson | Applied To |
|------|-------|--------|------------|
| 2026-04-05 | Builder | **Verify tool availability before scripting**: `jq` was not installed at build time. Scripts with external dependencies should check for the tool and emit a clear error — and the MVP template should list runtime prerequisites under `tests_required` or a new `prerequisites` field. | All future Builder tasks |
| 2026-04-05 | ProjectManager | **Execute agents sequentially with queue.json as shared state**: The queue.json file is the effective handoff contract between agents — each agent reads status and assigned_to to know what to do. Keeping it updated after every step prevents context drift in multi-step pipelines. | All future pipelines |
| 2026-04-05 | Tester | **Test with fixtures, not just live data**: Running tests against the real queue.json ties test results to live system state. Always test with at least one controlled fixture (empty queue, seeded queue) to make acceptance criteria provable independently of current system state. | All future Tester runs |

