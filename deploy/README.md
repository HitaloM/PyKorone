# Podman deployment

Use the [README setup](../README.md#podman) first. The supported deployment is Linux with a user systemd manager,
Podman >= 5.4, cgroup v2, and rootless UID/GID mappings in `/etc/subuid` and `/etc/subgid`.
`podman info --format '{{.Host.CgroupsVersion}} {{.Host.Security.Rootless}}'` should print `v2 true`.
No Docker daemon, Compose provider, privileged containers or Podman API socket is required.

## Lifecycle and configuration

`make podman-install` creates/replaces the `korone-config` Podman secret, installs `data/podman.env` with mode 0600
under `$XDG_CONFIG_HOME/korone` (default `~/.config/korone`), and links the Quadlet directory and `korone.target`
into the user configuration. It reloads systemd without starting the bot. Keep the checkout at that location;
rerun installation after moving it. The bot secret mounts the original dotenv bytes at `/app/data/config.env`
with UID/GID 101 and mode 0400, preserving Pydantic's dotenv and JSON-array parsing.
Systemd reads the infrastructure env file and passes only `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` to the API
and only `TUNNEL_TOKEN` to cloudflared. Quoted values in the examples are supported. Do not use shell expansion
or Compose `${VARIABLE}` interpolation in either file; write literal values.

`make podman-up` starts `korone.target`. PostgreSQL and Redis use `Notify=healthy`; the bot's `After=` ordering
waits for their healthchecks. The Bot API starts after the upload initializer. If a dependency becomes unavailable,
the bot's `Wants=` relationships keep its systemd restart policy active while dependencies recover.
Long-running services use `Restart=always` and retry after five seconds. PostgreSQL and Redis health failures
kill the container so systemd can restart it. Startup allows 15 minutes for pulls, builds and database setup.
`RunInit=true` reaps child processes in the bot. Podman allows 90 seconds for its graceful shutdown within
systemd's 120-second stop timeout. Container logs explicitly use journald for `make podman-logs`.

`make podman-down` stops all running stack containers, including the optional tunnel, through `PartOf=korone.target`.
Images, secrets, network and named volumes are retained. Redis remains an ephemeral cache, as in the previous
Compose deployment. Enable the regular target with `systemctl --user enable korone.target`; generated Quadlet
services themselves cannot be enabled. `loginctl enable-linger "$USER"` keeps the user manager running after logout
and starts it at boot (your host policy may require administrator authorization).

## Updates

After changing code or the Containerfile:

```sh
make podman-build
systemctl --user restart korone-bot.service
```

The `.build` unit builds `localhost/pykorone:latest` from the checkout with layer caching; the Containerfile
uses uv's locked dependencies, a separate runtime stage and a uv cache mount. The existing metadata `COPY`
avoids SELinux problems from mounting host metadata into build containers. The bot never pulls this local image.

After editing `data/config.env` or `data/podman.env`:

```sh
make podman-config
systemctl --user restart korone-telegram-api.service korone-bot.service
# If the tunnel is in use:
systemctl --user restart korone-tunnel.service
```

Replacing a secret requires recreating the container to consume its new contents. A systemd restart does that.
Changes to Quadlet definitions require `systemctl --user daemon-reload` before restarting affected services.
Dependency image updates are explicit: `podman pull` the fully qualified image from the relevant `.container`
file, then restart that service. Keep PostgreSQL on major version 18 until performing a database upgrade.
The default PostgreSQL database/user/password remain `korone` for compatibility with the old private Compose
network. If changing credentials, update both PostgreSQL's definition and the bot's `DB_URL` via Quadlet drop-ins;
changing `POSTGRES_PASSWORD` alone does not rotate an existing database password.

## Optional tunnel

Configure the credentials and webhook settings described in the README, refresh configuration, and start
`korone-tunnel.service`. The tunnel has no default install dependency. To start it with the stack on future boots,
add a Quadlet drop-in. Generated services cannot be enabled with `systemctl enable` or `systemctl add-wants`;
Quadlet processes their `[Install]` section during generation instead:

```sh
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/containers/systemd/korone-tunnel.container.d"
cat > "${XDG_CONFIG_HOME:-$HOME/.config}/containers/systemd/korone-tunnel.container.d/10-autostart.conf" <<'EOF'
[Install]
WantedBy=korone.target
EOF
systemctl --user daemon-reload
systemctl --user start korone.target korone-tunnel.service
```

The drop-in remains outside the repository even when the base Quadlets are linked through the `pykorone`
subdirectory. Enable `korone.target` and lingering as described above. To remove the tunnel's persistent dependency:

```sh
systemctl --user stop korone-tunnel.service
rm "${XDG_CONFIG_HOME:-$HOME/.config}/containers/systemd/korone-tunnel.container.d/10-autostart.conf"
systemctl --user daemon-reload
```

## Storage and security

All containers run under the same deployment user's default rootless user namespace. Do not add `UserNS=auto`
or per-container UID maps: UID 101 must refer to the same identity in the bot and API containers.
The runtime image's standalone user remains `korone` (999); Quadlet runs the bot as 101:101 to match the API image.
The upload initializer runs as container root inside that rootless namespace and prepares mode 0700 ownership
before the bot or API starts. It also runs for volumes restored from backups.

| Podman volume | Mount and ownership |
| --- | --- |
| `korone-postgres` | PostgreSQL 18 layout at `/var/lib/postgresql`; private SELinux label `:Z`. |
| `korone-telegram-data` | API read/write and bot read-only at `/var/lib/telegram-bot-api`; shared SELinux label `:z`. |
| `korone-telegram-uploads` | Bot read/write and API read-only at `.../korone-uploads`; UID/GID 101:101, mode 0700, shared `:z`. |

The separate upload volume prevents granting the bot write access to API downloads. The same absolute paths
are configured for aiogram's file wrapper. Provision disk for media workspaces and FFmpeg input/output;
concurrency limits do not impose a storage quota. Hard stops can leave files requiring manual cleanup.
No service publishes host ports; services communicate through aliases on the dedicated `korone` bridge network.
The bot and tunnel drop Linux capabilities and prevent privilege escalation. API and PostgreSQL retain the
capabilities required by their upstream initialization paths.

## Diagnostics

```sh
systemctl --user status korone.target korone-bot.service korone-postgres.service korone-redis.service
journalctl --user -u 'korone-*.service' -n 100
podman ps --all
podman healthcheck run korone-postgres
podman healthcheck run korone-redis
```

For generator errors, use your distribution's `podman-system-generator` (often `/usr/lib/systemd/system-generators/`
or `/usr/libexec/podman/quadlet`):

```sh
QUADLET_UNIT_DIRS="$PWD/deploy/quadlet" /usr/libexec/podman/quadlet --user --dryrun
```

Inspect the generated services after `daemon-reload` with `systemctl --user cat korone-bot.service`.
If startup times out while downloading images, pre-pull the upstream images and build with `make podman-build`.
If `podman info` fails, resolve the host's rootless runtime/storage permissions before starting systemd units.

The implementation follows the official [Quadlet reference](https://docs.podman.io/en/stable/markdown/podman-systemd.unit.5.html),
[build reference](https://docs.podman.io/en/stable/markdown/podman-build.1.html),
[secret creation](https://docs.podman.io/en/stable/markdown/podman-secret-create.1.html), and
[volume import](https://docs.podman.io/en/stable/markdown/podman-volume-import.1.html) documentation.
