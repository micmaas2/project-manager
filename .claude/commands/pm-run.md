# /pm-run — Execute Next Pending Task

**Execution mode**: do not enter plan mode. This skill executes a task that is already planned and queued. Proceed directly to the Steps below without calling EnterPlanMode.

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

Run each stage in sequence. At the marked boundaries, call `/compact` to clear accumulated context before spawning the next stage.

**5a. Builder**
Spawn Builder with task_id and artefact_path. Wait for Builder to deliver its artefact (script, patch, or plan). Confirm the expected output file exists in artefact_path.

**→ /compact** ← call here, after Builder artefact confirmed, before spawning Reviewer

**5b. Reviewer + code-quality-reviewer** (parallel)
Spawn Reviewer YAML agent and code-quality-reviewer built-in in parallel. Combine findings: Builder loops only on findings ≥80 confidence. If a Builder loop is needed, spawn Builder again and wait for fix. Confirm both reviews complete.

**→ /compact** ← call here, after all Reviewer findings are resolved, before spawning Tester

**5c. Tester**
Spawn Tester with task_id. Wait for test_report.md with overall PASS verdict.

**5d. DocUpdater + docs-readme-writer** (parallel)
Spawn DocUpdater (owns CHANGELOG.md) and docs-readme-writer (owns README.md) in parallel. Wait for both.

**5e. SelfImprover**
Spawn SelfImprover with task_id. Wait for improvement_proposals.md.

**Research/analysis tasks** (e.g. "explore repo", "review skills", "skills-review"): require a minimum of 2 exploration rounds before producing the final BL item list. The second round must cover at least 3 skills/files not explored in the first round. First-pass results feel complete but typically miss 30–40% of patterns without a mandatory second pass.

**Next step suggestion**
After the pipeline completes, print one line:
- If more paused or pending tasks remain in queue.json → `Suggested next: /pm-run  (N tasks remaining)`
- Else if improvement proposals are pending → `Suggested next: /pm-propose  (all tasks done — review proposals)`
- Else → `Suggested next: /pm-close  (queue clear — close the sprint)`
