# Releasing qBittorrent Plus

HACS uses **GitHub Releases**. Each release should ship `qbittorrent_plus.zip` (built by the release workflow).

## Steps for a new version

1. **Bump version** in `custom_components/qbittorrent_plus/manifest.json`.
2. **Commit and push** to `main` — wait for **Validate** and **Hassfest**.
3. **Create a GitHub release**:
   - Tag: `v1.0.0` (recommended `v` prefix)
   - Title / notes: changelog
4. **Publish** — the Release workflow will:
   - Set `manifest.json` `version` from the tag
   - Build `custom_components/qbittorrent_plus.zip`
   - Attach the zip to the release

```bash
cd path/to/hacs-qbittorrent
gh release create v1.0.0 --title "v1.0.0" --notes "Initial release."
```

## How HACS picks versions

| Setup | Behavior |
|-------|----------|
| `zip_release: true` in `hacs.json` | Downloads `qbittorrent_plus.zip` from the release |
| No releases | Uses files from `main` |

`filename` in `hacs.json` must match the release asset name exactly (`qbittorrent_plus.zip`).

## Validation

Every push/PR to `main` runs HACS validation and Hassfest.

### Common CI failures

| Workflow | Error | Fix |
|----------|-------|-----|
| Hassfest | `extra keys not allowed @ data['homeassistant']` | Keep min HA version in `hacs.json` only, not `manifest.json` |
| Validate | `no valid topics` / `no description` | Set repo description and topics via `gh repo edit` |
| Validate | brand assets | Ensure `custom_components/qbittorrent_plus/brand/icon.png` exists |

### GitHub repository settings

```bash
gh repo edit zlatko-lakisic/hacs-qbittorrent \
  --description "Home Assistant HACS integration for qBittorrent (expanded WebUI API)" \
  --add-topic home-assistant \
  --add-topic homeassistant \
  --add-topic hacs \
  --add-topic hacs-integration \
  --add-topic integration \
  --add-topic qbittorrent
```
