<p align="center">
  <img src="https://raw.githubusercontent.com/zlatko-lakisic/hacs-qbittorrent/main/images/readme-hero.png" alt="qBittorrent Plus" width="256">
</p>

# qBittorrent Plus

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/zlatko-lakisic/hacs-qbittorrent/actions/workflows/validate.yml/badge.svg)](https://github.com/zlatko-lakisic/hacs-qbittorrent/actions/workflows/validate.yml)

Home Assistant custom integration that fully drives a **qBittorrent** WebUI — Core monitoring parity, Alt-style controls, rich services, and optional per-torrent entities for **active** downloads/uploads only.

## Features

- **Instance sensors:** status, connection, dl/ul speeds & limits, session + all-time transfer, ratio, free disk space, torrent counts (all / active / inactive / paused / errored / downloading / seeding / stalled / queued), longest ETA, versions
- **Switch:** alternative speed limits
- **Numbers:** current / normal / alt speed limits, listen port
- **Buttons:** pause all, resume all
- **Hybrid torrents:** dynamic child devices for active torrents (progress, speeds, ratio, ETA, size, seeds/peers, pause switch, recheck / reannounce / delete) with a configurable cap (default 25)
- **Services:** get torrents, add / pause / resume / delete / recheck / reannounce, categories & tags, share limits, speed limits

Domain: `qbittorrent_plus` — safe to install beside the official `qbittorrent` integration.

## Prerequisites

- qBittorrent with **Web UI** enabled
- Home Assistant **2024.8+**
- Network path from HA to the WebUI URL

## Installation

See [docs/INSTALL.md](docs/INSTALL.md) for manual copy, PowerShell install, and HACS custom-repo steps.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-to-ha.ps1 -ConfigRoot '\\your-ha-host\config'
```

## Configuration

1. Add integration **qBittorrent Plus**
2. Enter WebUI URL (e.g. `http://172.16.55.2:8082`), username, password, SSL verify
3. **Configure** options:
   - Expose active torrents as entities (default on)
   - Max active torrent entities (default 25)
   - Poll interval seconds (default 30)

## Entities

| Platform | Examples |
|----------|----------|
| Sensor | `sensor.qbittorrent_*_download_speed`, counts, free space, per-torrent progress |
| Switch | Alternative speed; per-torrent Running |
| Number | Download/upload limits, listen port |
| Button | Pause all / Resume all; per-torrent Recheck / Reannounce / Delete |

Exact entity IDs depend on the config entry title/device name.

## Services

All services live under `qbittorrent_plus.*`. Pass `config_entry_id` when multiple instances exist.

Useful calls:

- `qbittorrent_plus.get_torrents` — response with filtered torrent list
- `qbittorrent_plus.add_torrent` — magnets/URLs or base64 `.torrent`
- `qbittorrent_plus.pause_torrents` / `resume_torrents` / `delete_torrents`
- `qbittorrent_plus.set_speed_limits` — global or per-hash

## Releases

See [docs/RELEASE.md](docs/RELEASE.md).

## Repo layout

```
custom_components/qbittorrent_plus/   # integration
docs/                                # INSTALL + RELEASE
scripts/install-to-ha.ps1
tests/                               # helper unit tests
```

## License

MIT — see [LICENSE](LICENSE).
