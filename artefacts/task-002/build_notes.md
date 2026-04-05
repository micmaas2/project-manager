# Build Notes — task-002: Audit Log Summary Script

## Design Decisions

1. **jq-based parsing**: audit.jsonl is JSONL — jq is the natural tool. Extracts `.agent` and `.action` fields, pipes through `sort | uniq -c` for counting. No custom parsing needed.

2. **Graceful handling**: Missing file and empty file are separate checks (missing file vs zero-byte file). Both print an informative message and exit 0 — no errors for legitimate empty states.

3. **Optional log path argument**: Script accepts an optional first argument for the log file path, defaulting to `../../logs/audit.jsonl` relative to the script location. Makes it testable with fixture files without modifying source.

4. **`set -euo pipefail`**: Strict mode enabled. Any unexpected failure will abort the script with a non-zero exit rather than silently continuing.

5. **Column ordering**: Output columns are Count | Action | Agent (not Agent first) because the action is the primary grouping dimension for audit summaries — you typically want to answer "how many of each action type, and by whom".

6. **shellcheck**: Not installed on this system. Script reviewed manually for common shellcheck issues:
   - All variables quoted
   - Array expansion not needed
   - `set -euo pipefail` used
   - No command substitution in conditions without quoting
   - No `echo` with flags (using printf in awk)

## Prerequisites Verified
- jq 1.7 installed at /usr/bin/jq (requirement: >= 1.6) ✅
