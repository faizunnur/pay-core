# Contributing to PayCore

Everything lands on `main` through a pull request. There are no exceptions, and
that includes one-line changes.

## Branching

Trunk-based development with short-lived branches. `main` is always deployable;
every commit on it is a release candidate.

| Branch | Use it for | Example |
| --- | --- | --- |
| `feature/<initials>-<short-description>` | New work | `feature/rr-add-currency-validation` |
| `fix/<initials>-<short-description>` | Bug fixes | `fix/rr-null-merchant-id` |
| `hotfix/<initials>-<short-description>` | Production emergencies only | `hotfix/rr-revert-risk-scan` |

Keep branches short-lived. A branch that has been open for days is a merge
conflict waiting to happen.

## `main` is protected

- No direct pushes.
- A pull request and one approving review are required.
- The `build`, `test` and `lint` checks must pass.
- Your branch must be up to date with `main` before it can merge.
- Merges are **squash and merge** only. One pull request becomes one commit,
  which is one deployable unit, which is one thing you can roll back.

## Before you open a pull request

```bash
ruff check .
pytest
```

Both must pass locally. CI runs the same two commands, so a red pipeline over
something you could have caught in ten seconds just costs everyone time.

## The pull request itself

The template fills itself in when you open the PR. Complete every section, and
take the security and rollback parts seriously - they are the point of the
exercise, not paperwork.

The last item on the reviewer checklist is *"I would be comfortable being paged
for this at 3am"*. If you would not be, say so in the review. That is a
legitimate reason to request changes.

## Reviewing

- Read the diff first, then the description, then check that they agree.
- Ask about anything you do not understand. "I do not understand this" is useful
  review feedback, not an admission of anything.
- Approve when you would be comfortable owning the change, not when you are
  tired of looking at it.

## Adding yourself to the contributors list

Create your own file at `docs/contributors/<your-initials>.md`:

```markdown
# Firstname Lastname (initials)

- Role this week:
- What I want to get out of this course:
- Something I am good at that the team should use:
```

One file per person. No two branches touch the same file, so every pull request
merges cleanly.

## Found a security problem?

PayCore contains known, intentional weaknesses that are used as teaching material
later in the course. If you spot one, **open an issue** describing it rather than
a pull request fixing it. Getting a finding written down, triaged and prioritised
is the skill being practised.
