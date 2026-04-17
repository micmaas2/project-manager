# /pm-run — Execute Next Pending Task

Find and execute the next task through the full pipeline.

## Steps

**1. Find next task**
Read tasks/queue.json. Apply priority order:
- (a) Tasks with status=paused and resume_from set — pick oldest by created date.
- (b) Tasks with status=pending — sort by priority (P1 first, then P2, then P3), then by created date oldest first.
Pick the first match.

**2. Present task**
Display: id, title, doel, current status, assigned_to, token_estimate.

**3. Validate MVP template**
Read the task's mvp_template. Verify all fields are present and non-empty: doel, niet_in_scope, acceptatiecriteria, security_arch_impact, tests_required, definition_of_done, rollback_plan, incident_owner, privacy_dpia, cost_estimate.
If any field is missing or empty: stop and report which fields need completing before the task can run.

**4. Preflight token check**
Read token_estimate from the task. If token_estimate > 400000: halt with:
`ALERT: Task <id> estimated tokens (<n>) exceed 80% of project cap (500k). Reduce scope or split task before proceeding.`

**5. Execute pipeline**
Invoke the ProjectManager YAML agent with the task_id. The ProjectManager will run the full pipeline: Builder → [Reviewer + code-quality-reviewer] → Tester → [DocUpdater + docs-readme-writer] → SelfImprover.

**Research/analysis tasks** (e.g. "explore repo", "review skills", "skills-review"): require a minimum of 2 exploration rounds before producing the final BL item list. The second round must cover at least 3 skills/files not explored in the first round. First-pass results feel complete but typically miss 30–40% of patterns without a mandatory second pass.

**Next step suggestion**
After the pipeline completes, print one line:
- If more paused or pending tasks remain in queue.json → `Suggested next: /pm-run  (N tasks remaining)`
- Else if improvement proposals are pending → `Suggested next: /pm-propose  (all tasks done — review proposals)`
- Else → `Suggested next: /pm-close  (queue clear — close the sprint)`
