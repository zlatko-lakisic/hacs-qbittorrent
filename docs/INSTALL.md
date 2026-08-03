# Install qBittorrent Plus in Home Assistant

## Before you start

1. Enable the **qBittorrent Web UI** (Tools → Options → Web UI).
2. Note the URL (e.g. `http://172.16.55.2:8082`) and credentials.
3. Home Assistant must be able to reach that URL on your LAN.

You can keep the official **qBittorrent** integration installed while testing — this integration uses domain `qbittorrent_plus` and will not collide. Migrate dashboards, then remove Core when ready.

---

## Option A — Install now (manual copy)

### From this repo (Windows + NAS share)

```powershell
cd path\to\hacs-qbittorrent
powershell -ExecutionPolicy Bypass -File scripts\install-to-ha.ps1 -ConfigRoot '\\your-ha-host\config'
```

### Manual copy

Copy `custom_components/qbittorrent_plus` to `<HA config>/custom_components/qbittorrent_plus`.

### After copy

1. **Restart Home Assistant**
2. **Settings → Devices & services → Add integration → qBittorrent Plus**
3. Enter WebUI **URL**, **Username**, **Password**, and SSL verify flag
4. Optionally open **Configure** on the integration to tune active-torrent exposure and poll interval

---

## Option B — HACS (custom repository)

1. Install [HACS](https://hacs.xyz/docs/setup/download) if needed.
2. HACS → **⋮** → **Custom repositories**
3. Repository: `https://github.com/zlatko-lakisic/hacs-qbittorrent`
4. Category: **Integration** → **Add**
5. Download **qBittorrent Plus** → **Restart Home Assistant**
6. Add the integration (same as Option A)

### Updates

HACS → Integrations → qBittorrent Plus → **Update** after a new [GitHub Release](RELEASE.md).

---

## Verify

You should see a **qBittorrent Plus** service device with:

- Status / speeds / torrent counts / free space sensors
- Alternative speed switch
- Pause all / Resume all buttons
- Speed limit number entities (some disabled by default)
- Active torrent child devices when downloads/uploads are in progress (if hybrid mode is on)

Services under **Developer tools → Services** are prefixed `qbittorrent_plus.`.
