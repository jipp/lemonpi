# lemonpi

Setup and maintenance for a Raspberry Pi based home server ("lemonpi").

The server runs a stack of Docker services (Home Assistant, ESPHome, Nginx
reverse proxy, Certbot, OctoPrint, Minecraft) on a custom Raspberry Pi OS
image booting from NVMe. ESPHome device configs for various M5Stack / ESP32
nodes are kept here too, along with a Python maintenance CLI.

## Repository layout

```
.
├── docker/      Docker Compose stack + Docker install helper
├── nginx/       Nginx reverse-proxy configuration (conf.d)
├── esphome/     ESPHome device configs and reusable common/ snippets
├── raspios/     Raspberry Pi OS image build/customization (bookworm, trixie)
└── scripts/     tools.py maintenance CLI + tools.ini config
```

## Components

### docker/
- `compose.yaml` — the full service stack:
  - **homeassistant** — Home Assistant (host network, D-Bus access).
  - **esphome** — ESPHome dashboard/CLI (run on demand, `manual` profile).
  - **nginx** — reverse proxy terminating TLS, resource-limited and hardened.
  - **certbot** — Let's Encrypt certificate issuance/renewal (`manual` profile).
  - **octoprint** — 3D printer control with MJPG camera streaming.
  - **minecraft-server** / **minecraft-server-small** — two vanilla servers
    (ports 25565 / 25566) each with a companion **mc-backup** container.
  - Shared JSON log rotation (`10m` × 3) to protect the SD card.
  - Per-service bridge networks with IPv6 enabled.
- `installDocker.sh` — installs Docker via the convenience script, adds the
  user to the `docker` group, enables memory cgroups, and documents the
  `daemon.json` (IPv6, live-restore, custom address pools).

### nginx/
Reverse-proxy config mounted read-only into the nginx container
(`/docker/nginx/conf.d`):
- `00-maps.conf` — shared `map` blocks (WebSocket upgrade handling, log
  filtering of OctoPrint polling).
- `homeassistant.conf` — local HTTP access plus external HTTPS vhost with
  OCSP stapling and HSTS.
- `octoprint.conf` — local HTTP and HTTPS access protected by HTTP basic auth.
- `snippets/` — reusable `proxy_pass` include files.

### esphome/
ESPHome firmware configurations:
- `basement.yaml`, `livingroom.yaml` — active device definitions.
- `common/` — reusable building blocks (base config, Wi-Fi/API/OTA, SPI/I2C
  busses, fonts, sensors, debug/diagnostic entities, etc.) pulled in via
  `substitutions` and packages.
- `dev/` — experimental / work-in-progress device configs.
- `run.sh` — run the ESPHome container directly against the current dir.

### raspios/
Scripts and cloud-init/custom config to build a customized Raspberry Pi OS
image that boots from NVMe:
- `createImage.sh` — validates the download checksum, decompresses, mounts the
  image via a loop device, applies boot/root partition tweaks from a release
  folder, then repacks and checksums the result.
- `afterInstall.sh` — first-boot steps: switch `cmdline.txt`/`fstab` from
  PARTUUID to the NVMe device, update packages, install git.
- `bookworm/custom.toml`, `trixie/` (`user-data`, `network-config`,
  `meta-data`, `pi-gen/`) — per-release provisioning (hostname, user, SSH,
  Wi-Fi, locale).

### scripts/
`tools.py` — a maintenance CLI driven by `tools.ini`. Runs from any directory
(it resolves its config relative to the script) and wraps common operations:

| Flag | Purpose | Example |
|------|---------|---------|
| `-s`, `--system`   | system health/info/update        | `tools.py -s update` |
| `-d`, `--docker`   | docker compose / prune / pull     | `tools.py -d "ps -a"` |
| `-c`, `--certbot`  | certbot run + nginx reload        | `tools.py -c "renew --dry-run"` |
| `-e`, `--esphome`  | esphome run against a yaml        | `tools.py -e "run basement.yaml"` |
| `-m`, `--minecraft`| rcon command to running servers   | `tools.py -m "say hello"` |
| `-b`, `--backup`   | backup apps / settings, copy out  | `tools.py -b execute` |
| `-n`, `--dry-run`  | print commands without running    | |
| `-V`, `--verbose`  | echo executed commands            | |

Backup subcommands: `execute` (tar each app under `src` into `dst`),
`settings` (archive dotfiles such as `.ssh`/`.gitconfig`), `local` (scp to a
mounted target), `remote` (scp to a remote server), `list`.

`tools.ini` holds the configuration (service folders, backup source/target,
local/remote scp targets, Minecraft container name, system commands). If it is
missing, `tools.py` writes a default one on first run.

> Note: `[system]` commands in `tools.ini` run through a shell, so anyone who
> can edit that file gets arbitrary command execution — keep it writable only
> by the server owner.

## Usage

Maintenance commands (run on the Pi):

```sh
# update the OS
scripts/tools.py -s update

# bring the stack up / check status
scripts/tools.py -d up -d        # docker compose up -d
scripts/tools.py -d "ps -a"

# renew certificates and reload nginx
scripts/tools.py -c renew

# flash an ESPHome device
scripts/tools.py -e "run basement.yaml"

# back up all apps, then copy to the remote server
scripts/tools.py -b execute
scripts/tools.py -b remote
```

## License

See [LICENSE](LICENSE).
