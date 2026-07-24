# Module Package Contract

These rules describe the runtime contract enforced by `korone.modules.load_modules` and `LoadedModule.from_module`.

## Required Manifest

- Every loadable `src/korone/modules/<module>/__init__.py` must expose one `manifest: ModuleManifest`.
- Utility packages such as `utils_` are exempt when absent from `korone.modules.MODULES`.
- Do not use the removed dunder metadata contract or a standalone package `setup()` function.

Use this shape:

```python
manifest = ModuleManifest(
    package=ModulePackage(...),
    router=router,
    handlers=(HandlerA, HandlerB),
)
```

## Discovery and Load Order

- Add each new loadable slug to the ordered `MODULES` tuple in `src/korone/modules/__init__.py`.
- Keep utilities out of `MODULES`.
- Preserve intentional ordering because routers and handlers are attached in that order.
- Treat configuration inclusion and exclusion as selectors over `MODULES`, not alternate registration.

## Router and Handlers

- Define a named `Router` for modules that register handlers or middleware.
- Pass it through `ModuleManifest(router=router)`.
- Store handler classes in a tuple, including a trailing comma for one handler.
- Use the handler bases and registration model described in `handlers-aiogram.md`.

## Package Metadata

- Provide `name`, `icon`, `summary`, `description`, and `public` through `ModulePackage`.
- Localize public metadata with `lazy_gettext as l_`.
- Use `LazyProxy` and STFU `Doc` for lazy structured descriptions.
- Use plain strings with `public=False` for internal modules where appropriate.

## Optional Contracts

- Use `ModuleScripts(pre_setup=..., post_setup=...)` for lifecycle hooks.
- Use `stats=<provider>` for statistics.
- Use `ModuleExport(provider, private_only=True)` for data export.
- Import `ModuleRegistry` for typed post-setup hooks.

`pre_setup()` receives no arguments. `post_setup(modules: ModuleRegistry)` receives the loaded mapping. Hooks may be synchronous or asynchronous, run concurrently within their phase, and must not depend on sibling hook order.

## Validation

- Import the new or changed package directly.
- Verify `LoadedModule.from_module(...)` accepts its `manifest`.
- Verify the slug, router, handler tuple, callbacks, hooks, stats, and export contracts affected by the change.
- Verify loader order and localization when package metadata changes.
