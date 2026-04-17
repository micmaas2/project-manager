# Improvement Proposals: task-036

## Proposal 1

**Target file**: `.claude/agents/reviewer.yaml`

**Change**: Move the confidence definition block (3 prose lines) outside the code-fence template to a dedicated "Field Definitions" subsection after the closing triple-backtick, so it is unambiguously a meta-instruction to the agent rather than template output.

**Rationale**: The current placement embeds free-prose instructions inside the output template code-fence. A reviewer reading the code-fence could misinterpret the prose as text to be included verbatim in review.md. A clearly separated "Field Definitions" subsection eliminates the ambiguity.

**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 2

**Target file**: `.claude/agents/builder.yaml`

**Change**: Replace "When reviewing findings from reviewer.yaml:" with "When processing Reviewer findings in review.md:" to reference the artefact Builder actually reads rather than the agent definition filename.

**Rationale**: The current phrasing couples the Builder instruction to the agent's filename. If reviewer.yaml is ever renamed, the instruction silently becomes inaccurate. Referencing review.md (the output artefact) is more resilient and describes what Builder actually interacts with.

**Status**: REQUIRES_HUMAN_APPROVAL
