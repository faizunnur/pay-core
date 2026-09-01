## What does this change?

<!-- One or two sentences. What behaviour is different after this merges? -->

## Why?

<!-- Link the issue, or explain the trigger. -->

## How was it tested?

- [ ] Unit tests added or updated
- [ ] `pytest` passes locally
- [ ] `ruff check .` passes locally
- [ ] Tested manually against the local stack (describe below)

<!-- Describe your manual test here -->

## Security considerations

- [ ] No secrets, tokens, keys or credentials in this diff
- [ ] No new third-party dependencies (if there are, list them and why)
- [ ] Input from users is validated before use
- [ ] Nothing sensitive is written to logs

## Risk & rollback

**Blast radius if this is wrong:**
<!-- Who or what breaks? Payments? One endpoint? Nothing user-facing? -->

**How to roll this back:**
<!-- Usually "revert this commit", but say so explicitly. -->

## Reviewer checklist

- [ ] I understand what this change does without asking the author
- [ ] The tests actually test the change
- [ ] I would be comfortable being paged for this at 3am
