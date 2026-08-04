"""Helper functions for qBittorrent Plus."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping, cast

from .const import (
    ACTIVE_TORRENT_STATES,
    DOWNLOADING_STATES,
    ERROR_STATES,
    INACTIVE_STATES,
    PAUSED_STATES,
    QUEUED_STATES,
    SEEDING_STATES,
    STALLED_STATES,
)


def normalize_url(url: str) -> str:
    """Normalize a WebUI URL for unique_id use."""
    return url.strip().rstrip("/").lower()


def seconds_to_hhmmss(seconds: Any) -> str | None:
    """Convert seconds to HH:MM:SS; return None for unknown/infinite ETA."""
    try:
        value = int(seconds)
    except (TypeError, ValueError):
        return None
    if value <= 0 or value >= 8640000:
        return None
    minutes, secs = divmod(value, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(secs):02}"


def format_unix_timestamp(timestamp: Any) -> str | None:
    """Format a UNIX timestamp to ISO-8601 UTC."""
    try:
        value = int(timestamp)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return datetime.fromtimestamp(value, tz=UTC).isoformat()


def format_torrent(torrent: Mapping[str, Any]) -> dict[str, Any]:
    """Format a single torrent for service responses."""
    progress = float(torrent.get("progress") or 0) * 100
    ratio = float(torrent.get("ratio") or 0)
    tags = torrent.get("tags") or ""
    if isinstance(tags, list):
        tags = ", ".join(str(t) for t in tags)
    return {
        "hash": torrent.get("hash"),
        "name": torrent.get("name"),
        "added_date": format_unix_timestamp(torrent.get("added_on")),
        "percent_done": f"{progress:.2f}",
        "progress": round(progress, 2),
        "status": torrent.get("state"),
        "eta": seconds_to_hhmmss(torrent.get("eta")),
        "eta_seconds": torrent.get("eta"),
        "ratio": round(ratio, 2),
        "category": torrent.get("category") or "",
        "tags": tags,
        "save_path": torrent.get("save_path") or torrent.get("savepath") or "",
        "size": torrent.get("size"),
        "total_size": torrent.get("total_size"),
        "dlspeed": torrent.get("dlspeed"),
        "upspeed": torrent.get("upspeed"),
        "num_seeds": torrent.get("num_seeds"),
        "num_leechs": torrent.get("num_leechs"),
        "total_downloaded": torrent.get("downloaded"),
        "total_uploaded": torrent.get("uploaded"),
    }


def format_torrents(torrents: Any) -> dict[str, dict[str, Any]]:
    """Format a list/dict of torrents keyed by name (fallback to hash)."""
    result: dict[str, dict[str, Any]] = {}
    items: list[Mapping[str, Any]]
    if isinstance(torrents, Mapping):
        items = list(torrents.values())
    else:
        items = list(torrents)
    for torrent in items:
        key = str(torrent.get("name") or torrent.get("hash") or len(result))
        result[key] = format_torrent(torrent)
    return result


def count_torrents_in_states(
    torrents: Mapping[str, Mapping[str, Any]] | None,
    states: set[str] | frozenset[str] | list[str] | None,
) -> int:
    """Count torrents whose state is in states; empty/None states = all."""
    if not torrents:
        return 0
    if not states:
        return len(torrents)
    state_set = set(states)
    return sum(1 for t in torrents.values() if t.get("state") in state_set)


def derive_counts(torrents: Mapping[str, Mapping[str, Any]] | None) -> dict[str, int]:
    """Derive aggregate torrent counts from sync maindata torrents map."""
    return {
        "all": count_torrents_in_states(torrents, None),
        "active": count_torrents_in_states(torrents, ACTIVE_TORRENT_STATES),
        "inactive": count_torrents_in_states(torrents, INACTIVE_STATES),
        "paused": count_torrents_in_states(torrents, PAUSED_STATES),
        "errored": count_torrents_in_states(torrents, ERROR_STATES),
        "downloading": count_torrents_in_states(torrents, DOWNLOADING_STATES),
        "seeding": count_torrents_in_states(torrents, SEEDING_STATES),
        "stalled": count_torrents_in_states(torrents, STALLED_STATES),
        "queued": count_torrents_in_states(torrents, QUEUED_STATES),
    }


def longest_eta_seconds(torrents: Mapping[str, Mapping[str, Any]] | None) -> int | None:
    """Return longest finite ETA among torrents, or None."""
    if not torrents:
        return None
    values: list[int] = []
    for torrent in torrents.values():
        try:
            eta = int(torrent.get("eta") or 0)
        except (TypeError, ValueError):
            continue
        if 0 < eta < 8640000:
            values.append(eta)
    return max(values) if values else None


def is_active_torrent(torrent: Mapping[str, Any]) -> bool:
    """Return True if torrent state qualifies for dynamic entity exposure."""
    return str(torrent.get("state") or "") in ACTIVE_TORRENT_STATES


def select_active_torrents(
    torrents: Mapping[str, Mapping[str, Any]] | None,
    max_entities: int,
) -> dict[str, Mapping[str, Any]]:
    """Select up to max_entities active torrents by speed then added_on."""
    if not torrents or max_entities <= 0:
        return {}

    active: list[tuple[str, Mapping[str, Any]]] = [
        (hash_, torrent)
        for hash_, torrent in torrents.items()
        if is_active_torrent(torrent)
    ]

    def sort_key(item: tuple[str, Mapping[str, Any]]) -> tuple[int, int]:
        torrent = item[1]
        try:
            speed = int(torrent.get("dlspeed") or 0) + int(torrent.get("upspeed") or 0)
        except (TypeError, ValueError):
            speed = 0
        try:
            added = int(torrent.get("added_on") or 0)
        except (TypeError, ValueError):
            added = 0
        return (speed, added)

    active.sort(key=sort_key, reverse=True)
    selected = active[:max_entities]
    return {hash_: torrent for hash_, torrent in selected}


def torrent_display_name(torrent: Mapping[str, Any], hash_: str) -> str:
    """Human-readable torrent name truncated for entity names."""
    name = str(torrent.get("name") or hash_[:8]).strip()
    if len(name) > 64:
        return f"{name[:61]}..."
    return name


def hashes_csv(hashes: list[str] | str | None, default: str = "all") -> str:
    """Normalize hashes argument to pipe-separated string for qbittorrent-api."""
    if hashes is None:
        return default
    if isinstance(hashes, str):
        return hashes.strip() or default
    cleaned = [h.strip() for h in hashes if h and str(h).strip()]
    return "|".join(cleaned) if cleaned else default


def merge_sync_maindata(
    previous_torrents: dict[str, dict[str, Any]],
    sync_data: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Merge incremental sync/maindata torrents into a full map."""
    torrents = dict(previous_torrents)
    full_update = bool(sync_data.get("full_update"))
    incoming = sync_data.get("torrents") or {}
    if full_update or not previous_torrents:
        torrents = {
            str(hash_): dict(cast(Mapping[str, Any], data))
            for hash_, data in cast(Mapping[str, Any], incoming).items()
        }
        # Ensure hash key is present on each torrent dict.
        for hash_, data in torrents.items():
            data.setdefault("hash", hash_)
        return torrents

    for hash_, data in cast(Mapping[str, Any], incoming).items():
        key = str(hash_)
        existing = torrents.get(key, {})
        merged = dict(existing)
        merged.update(dict(cast(Mapping[str, Any], data)))
        merged.setdefault("hash", key)
        torrents[key] = merged

    for hash_ in sync_data.get("torrents_removed") or []:
        torrents.pop(str(hash_), None)

    return torrents


def merge_server_state(
    previous: dict[str, Any],
    sync_data: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge incremental sync/maindata server_state into a full map.

    Partial updates only include changed keys. Replacing the whole dict drops
    fields like dl_info_speed/up_info_speed when they are unchanged.
    """
    incoming = sync_data.get("server_state")
    if sync_data.get("full_update") or not previous:
        return dict(incoming) if incoming else dict(previous)
    if not incoming:
        return dict(previous)
    merged = dict(previous)
    merged.update(dict(cast(Mapping[str, Any], incoming)))
    return merged
