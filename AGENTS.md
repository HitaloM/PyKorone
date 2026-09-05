# PyKorone Codex Instructions

## Repository Context

PyKorone is a modular Telegram bot built with Python, aiogram, PostgreSQL, Redis, SQLAlchemy async, Alembic, Ruff, Pyright, uv, and gettext catalogs. Treat `pyproject.toml` and `.python-version` as the sources of truth for the supported and local Python versions.

Keep repository guidance small and durable here. Use the domain skills under `.agents/skills/` for detailed workflows.
Keep detailed decisions and their rationale in the relevant skill references, with basic developer setup in the README.

## Default Workflow

- Read the nearest existing implementation and the relevant skill references before editing. Preserve domain
  behavior while converging on canonical contracts; do not perpetuate a local workaround solely because it is nearby.
- Keep edits scoped to the requested behavior and avoid unrelated formatting churn.
- Use `rg` or `rg --files` for searches.
- Use `uv` for project commands; do not introduce pip-only, poetry, or pipenv workflows.
- Do not revert user changes or dirty worktree changes unless explicitly asked.
- Prefer focused validation. Run broader checks when touching shared handlers, repositories, migrations, module loading, localization, or tooling.

## Common Commands

- Install dependencies: `uv sync --locked`
- Run the bot: `uv run python -m korone`
- Ruff lint: `uv run ruff check`
- Ruff format: `uv run ruff format`
- Type check: `uv run pyright`
- Automated tests: this project has no test suite. Do not create tests, test files, test fixtures, or introduce a test framework unless the user explicitly requests it. Validate with the smallest deterministic reproduction plus relevant Ruff and Pyright checks.
- Update locale catalogs: `make update_lang`
- Compile locale catalogs: `make compile_lang`
- Create Alembic revision: `make db_revision m="message"`
- Apply migrations: `make db_upgrade`

## Skill Routing

- Use `issue-fixer` as the primary workflow for bugs, regressions, exceptions, failing checks, and unexpected behavior.
- Use `review-aiogram-updates` as the primary workflow for assessing recent aiogram releases and their impact on PyKorone.
- Use `add-media-platform` as the primary workflow only for a completely new supported media platform.
- Use `create-korone-module` as the primary workflow only for a new top-level loadable module.
- Otherwise, use `py-korone-development` for implementation or review under `src/korone/` and for project tooling, loading only references relevant to the affected boundary.
- Add `localization-workflow` whenever user-facing strings or gettext catalogs change.
- Use `commit-by-scope` only when the user explicitly asks to create one or more commits.

## Code Review Rules

- Flag changes that bypass repository classes, project handler bases, module loader contracts, or the localization workflow.
- Flag structured output that stringifies UI expressions, restores HTML/parse-mode rendering, imports internal UI nodes,
  or depends on private aiogram formatting state; use `korone.ui` and project rendering boundaries instead.
- Require focused regression evidence for behavior changes and validation proportional to the affected boundary.
- Focus review comments on correctness, security, data flow, and project contracts; leave mechanically enforced formatting, lint, and typing findings to Ruff and Pyright.

## Project Rules

- New and edited Python functions must have complete type annotations using modern syntax.
- Prefer project handler bases from `korone.utils.handlers` over raw function-based aiogram handlers.
- Build structured user-facing content and module descriptions with `korone.ui`; pass UI or aiogram `Text` objects to
  project handler boundaries instead of converting them to strings, HTML, or parse-mode markup.
- Import `korone.ui.rendering` only at low-level Telegram payload boundaries. When changing the UI compiler or
  components, validate nested aiogram formatting, lazy expressions, and multiline indentation with entities intact.
- Keep database access behind repository classes and async SQLAlchemy sessions.
- Use structured logging through `korone.logger.get_logger`.
- Keep module package metadata and loader contracts stable.
- When strings shown to users change, update and manually review gettext catalogs in the same change.
- Use the entity's owning repository and explicit Telegram/database ID namespaces; never fall back between namespaces.
- Use project response helpers and central Telegram error predicates. Keep domain-specific transport fallbacks local.
- Keep deferred translations uncached and evaluate them in the current locale; do not copy Babel private state.
- Give asynchronous work an owner and shutdown path; use the shared subprocess runner for timeout/cancellation cleanup.
