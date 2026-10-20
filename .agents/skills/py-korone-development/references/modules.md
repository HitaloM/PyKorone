# Module manifests and loading

Sources: `src/korone/modules/metadata.py` and `src/korone/modules/__init__.py`. Verify these live contracts when changing
the loader or creating a module; a static scaffold is not authoritative.

## Manifest and discovery

Each loadable package exposes `manifest: ModuleManifest` and has a slug in the ordered `MODULES` tuple. Utility packages
such as `utils_` are not loadable and stay out of that tuple. Inclusion/exclusion config selects from this tuple; it does
not register extra packages. Preserve router/handler precedence from its order.

The manifest contains `ModulePackage` and only the optional capabilities needed by the module:

| Field | Contract |
| --- | --- |
| `router` / `handlers` | Named router and a tuple of project handler classes |
| `scripts` | `ModuleScripts(pre_setup=..., post_setup=...)` |
| `stats` | Provider returning a UI expression, synchronously or asynchronously |
| `export` | `ModuleExport(provider, private_only=...)`, receiving a Telegram chat ID |
| `inline_query` | `ModuleInlineQuery(provider, matcher=..., priority=..., timeout_seconds=...)`, returning `InlineQueryContribution` |

Do not restore removed dunder metadata or standalone package setup conventions. `LoadedModule.from_module(...)`
validates the manifest. `ModuleHandler` intentionally uses a narrow `Any` boundary because aiogram flag decorators erase
class types; do not spread that exception into feature values.

## Lifecycle

The loader imports selected packages, attaches routers, registers handlers, runs all pre-setup hooks, then all post-setup
hooks. `pre_setup()` takes no arguments; `post_setup(modules: ModuleRegistry)` receives loaded modules. Hooks may be sync
or async and run concurrently within each phase; they cannot depend on sibling order. Sync hooks may execute in threads.

Keep module middleware under `middlewares/` with intentional exports. Register it and related router startup/shutdown
observers in `pre_setup()` declared through `ModuleScripts`. Do not register them at import time. Instantiate resources
without starting unowned background work during import. `stickers` demonstrates owned processing jobs; `inline` builds
its provider registry in post-setup.

## Metadata and help

`ModulePackage` defines `name`, `icon`, `summary`, `description`, and `public`, with defaults for optional metadata.
Localize public text with `lazy_gettext as l_`. Structured descriptions use project `LazyProxy(lambda: column(...))`;
keep the expression deferred and uncached until help rendering. Internal modules may use plain text with `public=False`.
Use [text-ui.md](text-ui.md) for expression/rendering changes and the localization workflow for visible text changes.

## Validation

With controlled configuration, import affected packages and pass them to `LoadedModule.from_module(...)`. Use an isolated
dispatcher to validate changed router/handler registration and hooks. Check only introduced/changed capabilities and
verify metadata in alternating locales when changed. Import checks catch runtime inheritance/decorator failures that
static checking alone misses. Full bot startup is not required for these checks.
