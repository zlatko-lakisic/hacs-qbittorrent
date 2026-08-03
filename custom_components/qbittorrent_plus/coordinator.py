"""Data update coordinator for qBittorrent Plus."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    QBittorrentPlusApi,
    QBittorrentPlusAuthError,
    QBittorrentPlusConnectionError,
)
from .const import (
    CONF_EXPOSE_ACTIVE_TORRENTS,
    CONF_MAX_TORRENT_ENTITIES,
    CONF_SCAN_INTERVAL,
    DEFAULT_EXPOSE_ACTIVE_TORRENTS,
    DEFAULT_MAX_TORRENT_ENTITIES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .helpers import derive_counts, longest_eta_seconds, merge_sync_maindata, select_active_torrents

_LOGGER = logging.getLogger(__name__)


class QBittorrentPlusCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll qBittorrent sync/maindata and preferences."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        api: QBittorrentPlusApi,
        config_entry: ConfigEntry,
    ) -> None:
        self.api = api
        self.config_entry = config_entry
        self._rid = 0
        self._torrents: dict[str, dict[str, Any]] = {}
        self._categories: dict[str, Any] = {}
        self._tags: list[str] = []
        self._known_active_hashes: set[str] = set()
        scan = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            update_interval=timedelta(seconds=scan),
            config_entry=config_entry,
        )

    @property
    def expose_active_torrents(self) -> bool:
        """Whether dynamic active-torrent entities are enabled."""
        return bool(
            self.config_entry.options.get(
                CONF_EXPOSE_ACTIVE_TORRENTS, DEFAULT_EXPOSE_ACTIVE_TORRENTS
            )
        )

    @property
    def max_torrent_entities(self) -> int:
        """Maximum number of dynamic torrent entities."""
        try:
            return int(
                self.config_entry.options.get(
                    CONF_MAX_TORRENT_ENTITIES, DEFAULT_MAX_TORRENT_ENTITIES
                )
            )
        except (TypeError, ValueError):
            return DEFAULT_MAX_TORRENT_ENTITIES

    def selected_active_torrents(self) -> dict[str, dict[str, Any]]:
        """Return currently selected active torrents for entity exposure."""
        if not self.expose_active_torrents or not self.data:
            return {}
        selected = select_active_torrents(
            self.data.get("torrents"), self.max_torrent_entities
        )
        return {k: dict(v) for k, v in selected.items()}

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            sync_data = await self.hass.async_add_executor_job(
                self.api.sync_maindata, self._rid
            )
            preferences = await self.hass.async_add_executor_job(self.api.app_preferences)
            alt_enabled = await self.hass.async_add_executor_job(
                self.api.transfer_speed_limits_mode
            )
        except QBittorrentPlusAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except QBittorrentPlusConnectionError as err:
            raise UpdateFailed(f"Connection failed: {err}") from err

        self._rid = int(sync_data.get("rid") or 0)
        self._torrents = merge_sync_maindata(self._torrents, sync_data)

        if "categories" in sync_data:
            if sync_data.get("full_update"):
                self._categories = dict(sync_data.get("categories") or {})
            else:
                self._categories.update(dict(sync_data.get("categories") or {}))
            for name in sync_data.get("categories_removed") or []:
                self._categories.pop(str(name), None)

        if "tags" in sync_data:
            if sync_data.get("full_update"):
                self._tags = list(sync_data.get("tags") or [])
            else:
                for tag in sync_data.get("tags") or []:
                    if tag not in self._tags:
                        self._tags.append(tag)
            for tag in sync_data.get("tags_removed") or []:
                if tag in self._tags:
                    self._tags.remove(tag)

        server_state = dict(sync_data.get("server_state") or {})
        # Prefer server_state flag when present.
        if "use_alt_speed_limits" in server_state:
            alt_enabled = bool(server_state.get("use_alt_speed_limits"))

        counts = derive_counts(self._torrents)
        data: dict[str, Any] = {
            "server_state": server_state,
            "torrents": dict(self._torrents),
            "categories": dict(self._categories),
            "tags": list(self._tags),
            "preferences": dict(preferences or {}),
            "app_version": self.api.app_version,
            "api_version": self.api.api_version,
            "counts": counts,
            "longest_eta": longest_eta_seconds(self._torrents),
            "alt_speed_enabled": alt_enabled,
            "url": self.api.url,
        }
        return data

    @callback
    def async_update_listeners_active(self) -> set[str]:
        """Return active hashes after update; used by platforms for entity sync."""
        selected = set(self.selected_active_torrents())
        self._known_active_hashes = selected
        return selected


type QBittorrentPlusConfigEntry = ConfigEntry[QBittorrentPlusCoordinator]
