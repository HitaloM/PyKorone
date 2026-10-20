---
name: commit-by-scope
description: Create atomic Conventional Commits from authorized working-tree changes when the user explicitly asks to commit. Does not authorize pushing or rewriting history.
---

# Commit by Scope

Use only for an explicit commit request. Inspect `git status --short`, staged/unstaged diffs, and recent subjects to
identify the authorized change set and established scope names. Preserve pre-existing and unrelated work, including
staged content; do not include or unstage it just because it is present.

## Grouping and messages

Group by coherent intent. Keep implementation with its required migration, localization, generated artifacts, and
contract documentation. Split distinct purposes when each intermediate commit remains understandable and valid;
do not split mechanically by file or directory.

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):
`type(scope): imperative description`, omitting scope when no single owner exists. Choose the type from intent
(`feat`, `fix`, `refactor`, `perf`, `docs`, `build`, `ci`, `chore`, or an applicable authorized operation).
Use the owning feature/subsystem and established history for scope: a provider name for a provider-only change,
`medias` for the shared pipeline, or `agents`/`skills` for that maintenance. Avoid vague scopes like `misc` or `src`.

Add a body only for useful motivation, decisions, or constraints. Mark breaking changes with `!` and/or a
`BREAKING CHANGE:` footer. Pass actual paragraphs with separate `-m` arguments or a message file; do not embed literal
`\n` sequences in a subject argument.

## Commit execution

Stage one group at a time by explicit paths or patches. Before committing, inspect the staged names and full diff and
run `git diff --cached --check`. If unrelated index content cannot be isolated without disturbing user work, ask about
that specific conflict. Broad staging is appropriate only when every detected change belongs to the authorized group.

Commit without bypassing hooks or changing identity/signing configuration. If a hook fails, preserve the work and
diagnose it; fix only within the authorized scope. Do not claim checks passed unless they ran. Do not create empty
commits, amend, squash, rebase, discard work, or push without the corresponding explicit request.

After each commit, verify the remaining changes. Inspect stored final messages and report hashes/subjects and any
changes intentionally left uncommitted.
