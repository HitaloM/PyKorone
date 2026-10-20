# Project tooling and deployment configuration

Read active versions from project configuration. Use the [README](../../../../README.md#development) for basic setup and
[deployment guide](../../../../deploy/README.md) for Podman operations and diagnostics.

## Tool contracts

| Change | Keep aligned |
| --- | --- |
| Dependencies | `pyproject.toml` and `uv.lock`; manage with uv |
| Python version | Supported minimum, `.python-version`, `Containerfile`, documented requirements |
| Lint/format | `ruff.toml` and `.pre-commit-config.yaml`; compare actual hook/tool behavior |
| Schema tooling | `alembic.ini`, `alembic/env.py`, `db/utils.py`, Makefile; see [persistence.md](persistence.md) |
| Localization targets | Makefile extraction/update/obsolete cleanup/compile; use [localization-workflow](../../localization-workflow/SKILL.md) |
| Runtime/bootstrap | `korone/__init__.py`, `korone/__main__.py`, `config.py`; see [runtime.md](runtime.md) |
| Container deployment | `Containerfile`, `deploy/quadlet/`, `deploy/systemd/korone.target`, examples and deployment guide |

Ruff's `logger-objects` accepts fully qualified logger instances, not factories like `get_logger`. Avoid broad ignores or
changes to policy merely to silence a defect. Use a writable temporary `UV_CACHE_DIR` if the default cache is read-only;
`uv run --no-sync` is for an already synchronized environment, not a substitute for checking the lockfile.

## Deployment invariants

Keep the locked multi-stage Containerfile and `python -m korone` entrypoint. The supported stack is rootless Podman
Quadlet/systemd; Docker references describe migration, not a parallel Compose deployment. Keep image names fully
qualified and the checkout-relative Quadlet build context intact.

The bot and local Bot API share read-only downloads and a separate upload volume with complementary write permissions.
Preserve the shared UID/GID identity, initializer ordering, aiogram path mapping, and upload root containment. The
standalone image user and Quadlet user intentionally differ. Consult the deployment guide and live units for actual paths,
IDs, SELinux labels, and settings instead of copying them into new infrastructure.

Mount the bot's original dotenv bytes through its Podman secret so Pydantic parses them. Systemd forwards only required
infrastructure variables to each service. Module selectors are JSON arrays in `MODULES_LOAD` / `MODULES_NOT_LOAD`.
Keep `korone.target`, health readiness, restart ownership, and graceful shutdown consistent across units. Storage migration
between engines uses offline backup/restore, not interchangeable engine data directories.

## Validation

Run affected safe tool targets and check generated artifacts. For Quadlet edits inspect generator output, service ordering,
mount/secret ownership, and build paths. Run builds or service lifecycles only when the requested scope and environment
support them; otherwise report which checks remain unavailable. Documentation-only edits need link/structure checks,
not dependency installs, migrations, container startup, or full-project static checks.
