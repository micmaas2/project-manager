# Improvement Proposals — task-011

Agent: SelfImprover [Haiku]
Date: 2026-04-10

---

## Proposal 1

**Target file**: `CLAUDE.md` — MVP template section (`security_arch_impact` block or a new `cron_hardening` checklist)

**Change**: Add a cron/daemon shell script hardening block to the MVP template. Insert after the existing outbound-HTTP security bullets:

```
  - If the script runs under cron or systemd (no interactive terminal):
      - Log writability guard: verify/create log file before first write; exit to stderr if unwritable
      - Concurrency lock: use `flock -n` on a lock file at startup; skip (exit 0) if lock held
      - SSH/auth identity: export `GIT_SSH_COMMAND` or equivalent explicitly — cron env has no agent
      - Log rotation: document logrotate config as a **required** deploy step, not optional
```

**Rationale**: All four review-loop items in task-011 (CR-1 log guard, CR-2 SSH identity, m-2 flock, m-5 logrotate) are table-stakes for any cron-deployed shell script. They were not in the MVP template or acceptance criteria, so Builder omitted them and Reviewer caught them in pass 2. Adding them to the template surfaces the requirement at planning time (preflight), not at review time — eliminating the loop entirely for future cron tasks. This is the same systemic fix that was applied for outbound HTTP and YAML injection in earlier tasks.

**Status**: APPROVED

---

## Proposal 2

**Target file**: `CLAUDE.md` — Builder checklist / agent spawn guidance (or `self-improver.yaml` prompt)

**Change**: Add a pre-submission self-check instruction for Builder tasks that produce shell scripts:

```
**Shell script pre-submission check** (before handing off to Reviewer):
- `bash -n <script>` must exit 0
- If cron/daemon: log guard, flock, SSH identity, logrotate — all present?
- If outbound git/SSH: auth path exported explicitly?
- Log output sanitized (ANSI + control chars stripped) before writing to file?
```

**Rationale**: The code-quality-reviewer caught log injection (M-1) and stash-pop conflict risk (M-2) that a simple self-review checklist would have surfaced before any review agent ran. Builder currently has no explicit pre-handoff verification step for shell scripts. Adding one reduces first-pass review findings for bash tasks to only genuine design-level issues, not missing-guard patterns. This parallels the "test with fixtures" lesson applied to Tester — the right agent should catch the obvious failures before passing the baton.

**Status**: APPROVED
