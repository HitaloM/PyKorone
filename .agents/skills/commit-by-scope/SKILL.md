---
name: commit-by-scope
description: Create one or more atomic Git commits from existing working-tree changes, grouping them by coherent scope and intent and writing Conventional Commits messages. Use only when the user explicitly asks to commit changes, create commits, split changes into commits, or commit each scope separately. Do not use for ordinary implementation work, commit planning without execution, amending history, rebasing, pushing, or opening pull requests unless the user separately requests those actions.
---

# Commit by Scope

Commit only the changes the user authorized, preserving unrelated work and producing a reviewable sequence of Conventional Commits.

## Workflow

1. Inspect repository instructions and the complete working-tree state with `git status --short`, staged and unstaged diffs, and recent commit subjects.
2. Identify the requested change set. Treat pre-existing or ambiguous changes as user-owned; do not include, discard, rewrite, or unstage them merely because they are present.
3. Partition the requested changes by coherent intent and scope:
   - create one commit when all changes form one indivisible behavior or maintenance unit;
   - create multiple commits when groups have distinct purposes and each group remains valid and understandable on its own;
   - keep implementation and its directly required migrations, generated files, or localization updates together; include tests only when they already exist in the authorized change set or the user explicitly requested them;
   - do not split solely by file or directory when the files implement the same outcome;
   - order dependent commits so every intermediate commit is internally consistent.
4. Choose scopes from PyKorone's logical ownership and recent commit history:
   - use the user-facing module or shared subsystem that owns the behavior, not a filename or directory name chosen mechanically;
   - prefer established scopes such as `medias`, `db`, `redis`, `i18n`, `http`, `config`, `logging`, `telegram`, `dispatcher`, `handlers`, or `middleware` when the change belongs to that shared boundary;
   - use a top-level module name for module-owned behavior, and a media provider name for provider-specific behavior; reserve `medias` for behavior shared across providers;
   - when one coherent change crosses layers, scope it to the owning feature or module rather than a lower-level helper it happens to touch;
   - use `deps`, `ci`, `docs`, `agents`, or `skills` for repository maintenance only when that area is the actual subject of the commit;
   - reuse the most recent established spelling for a scope and write new multiword scopes in lowercase kebab-case;
   - omit the scope for genuinely repository-wide changes with no single logical owner. Do not invent vague scopes such as `core`, `misc`, `src`, or `changes`.
5. Choose the type from the actual intent:
   - `feat` for a user-visible capability;
   - `fix` for a defect correction;
   - `refactor` for behavior-preserving restructuring;
   - `perf` for a performance improvement;
   - `test` only for user-authorized, test-only changes already present in the requested change set;
   - `docs` for documentation-only changes;
   - `build` for build system or dependency changes;
   - `ci` for continuous-integration changes;
   - `chore` for maintenance not better described above;
   - `revert` for an explicitly requested revert.
6. Stage only the first planned group. Use path-level or patch-level staging when a file contains changes for multiple groups. Never use broad staging such as `git add .` unless every detected change is authorized and belongs to that commit.
7. Review the staged name list, statistics, full diff, and `git diff --cached --check`. If the index contains unrelated or ambiguous content that cannot be isolated safely, stop and ask the user how to proceed.
8. Commit with the format `type(scope): concise imperative description`, or `type: concise imperative description` when omitting scope. When the subject alone does not preserve enough useful context, add an optional body after a blank line. Use concise paragraphs or short lists to explain relevant context, motivation, decisions, impacts, or constraints; omit the body for straightforward commits and do not merely repeat the subject. When invoking Git non-interactively, pass the subject and each body paragraph with separate `-m` arguments or use a prepared message file; never embed escaped `\n` sequences in a `-m` argument. Mark a breaking change with `!` and/or a `BREAKING CHANGE:` footer.
9. Repeat staging, verification, and committing for each planned group. After every commit, confirm that the remaining working-tree changes match the uncommitted groups.
10. Inspect each final commit message as Git stored it, then report the resulting commit hashes and subjects, plus any changes intentionally left uncommitted.

## Safety Rules

- Require an explicit commit request; never commit as a side effect of implementing or reviewing code.
- Do not amend, squash, rebase, reset, restore, clean, delete, push, or force-push unless the user explicitly requests that separate action.
- Do not bypass hooks with `--no-verify` or change Git identity or signing configuration.
- Do not claim validation succeeded unless it was actually run. If a hook fails, preserve the working tree, diagnose the failure, and report it; fix it only when the requested scope authorizes the change.
- Do not create empty commits unless explicitly requested.
- Follow the [Conventional Commits 1.0.0 specification](https://www.conventionalcommits.org/en/v1.0.0/) and prefer established repository conventions where the specification leaves choices open.
