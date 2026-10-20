# PyKorone

Modular Telegram bot using aiogram, PostgreSQL, async SQLAlchemy, Redis, and gettext.
Read Python and dependency versions from `pyproject.toml`, `.python-version`, and `uv.lock`.
Developer setup lives in [README.md](README.md#development); deployment operations in [deploy/README.md](deploy/README.md).

## Workflows

Use the matching skill in [.agents/skills](.agents/skills). Choose the primary workflow by the requested outcome:

| Task | Skill |
| --- | --- |
| Diagnose or fix a bug, regression, or failing check | `issue-fixer` |
| Assess recent aiogram releases against this project | `review-aiogram-updates` |
| Add a completely new media provider | `add-media-platform` |
| Create a new loadable top-level module | `create-korone-module` |
| Other code or project-tooling implementation/review | `py-korone-development` |
| Add, change, or remove user-facing strings/catalogs | Also use `localization-workflow` |
| Create commits, when explicitly requested | `commit-by-scope` |

Specialized workflows link to shared development references; read only those needed for the affected contract.
Use current implementations to verify those contracts, without copying a nearby workaround automatically.
Keep changes scoped and preserve unrelated worktree changes. Use `rg` for searches and `uv` for project commands.

## Project contracts

- Fully annotate new and edited Python functions. Keep structured logging through `korone.logger.get_logger`.
- Prefer handler bases from `korone.utils.handlers`; use project response helpers and central Telegram error predicates.
  Keep domain-specific transport fallbacks in their owning adapter.
- Compose structured output and module descriptions with `korone.ui`. Pass expressions or aiogram `Text` to project
  helpers; render only at Telegram payload boundaries through `korone.ui.rendering`. Preserve entities without
  stringifying expressions, HTML/parse-mode rendering, internal UI node imports, or private aiogram formatting state.
- Keep feature SQL and transactions in repositories. Distinguish Telegram IDs from database keys explicitly and use
  the entity's owning repository; never retry a lookup in a different ID namespace.
- Preserve module manifests and loader contracts. Shared runtime resources and background tasks need an owner and
  shutdown path; subprocesses use `korone.utils.subprocess.run_process` for timeout/cancellation cleanup.
- Update and manually review gettext catalogs with visible string changes. Deferred translations remain uncached and
  resolve in the current locale; do not copy Babel private state.

## Commands and validation

| Purpose | Command |
| --- | --- |
| Install locked dependencies | `uv sync --locked` |
| Lint / check formatting | `uv run ruff check <paths>` / `uv run ruff format --check <paths>` |
| Type check | `uv run pyright` |
| Update / compile catalogs | `make update_lang` / `make compile_lang` |
| Generate migration | `make db_revision m="message"` |
| Apply migrations | `make db_upgrade` |
| Run the bot | `uv run python -m korone` |

The project has no automated test suite. Do not create tests, test files, fixtures, or a test framework unless the
user explicitly requests them. Use the smallest deterministic reproduction for behavior changes and the relevant
Ruff/Pyright checks. Broaden validation for shared handlers, repositories, migrations, loading, localization, or runtime.
Documentation-only changes need structural/link checks. Bot startup connects to services, applies migrations, and drops
pending Telegram updates; use controlled reproductions for smoke checks. Report unverified behavior explicitly.

## Code Review Rules

Flag changes that bypass repository ownership, handler/loader contracts, localization, or public UI/rendering boundaries.
Focus on correctness, security, data flow, and project contracts. For behavior changes, require focused regression evidence
proportional to the affected boundary. For UI/compiler changes, check nested aiogram formatting, lazy expressions, and
multiline indentation with entities intact.
Leave mechanically enforced formatting, lint, and typing findings to Ruff and Pyright.

## Maintaining guidance

Keep durable repository rules here and conditional workflows/decisions in the relevant skill reference. Update guidance
when its contract changes; avoid generic Python tutorials, copied API manuals, and duplicated operational instructions.
Follow OpenAI's [AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md) and
[skill authoring guidance](https://learn.chatgpt.com/docs/build-skills): concise discovery descriptions and references
loaded only when relevant.
