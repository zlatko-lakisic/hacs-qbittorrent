"""Switches for qBittorrent Plus."""

from __future__ import annotations

from typing import Any, Mapping

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PAUSED_STATES
from .coordinator import QBittorrentPlusConfigEntry, QBittorrentPlusCoordinator
from .entity import QBittorrentPlusEntity, QBittorrentPlusTorrentEntity
from .helpers import torrent_display_name
from .torrent import TorrentEntityManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: QBittorrentPlusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switches."""
    coordinator = entry.runtime_data
    async_add_entities([QBittorrentPlusAltSpeedSwitch(coordinator)])

    manager = TorrentEntityManager(coordinator, async_add_entities)

    def make_entities(torrent_hash: str, torrent: Mapping[str, Any]) -> list:
        name = torrent_display_name(torrent, torrent_hash)
        return [QBittorrentPlusTorrentPauseSwitch(coordinator, torrent_hash, name)]

    manager.register(DOMAIN, "switch", make_entities)
    manager.async_sync()
    entry.async_on_unload(coordinator.async_add_listener(manager.async_sync))


class QBittorrentPlusAltSpeedSwitch(QBittorrentPlusEntity, SwitchEntity):
    """Toggle alternative speed limits."""

    _attr_translation_key = "alternative_speed"

    def __init__(self, coordinator: QBittorrentPlusCoordinator) -> None:
        super().__init__(coordinator, "alternative_speed")

    @property
    def is_on(self) -> bool:
        """Return True if alternative speed limits are enabled."""
        return bool((self.coordinator.data or {}).get("alt_speed_enabled"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable alternative speed limits."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.toggle_speed_limits_mode, True
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable alternative speed limits."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.toggle_speed_limits_mode, False
        )
        await self.coordinator.async_request_refresh()


class QBittorrentPlusTorrentPauseSwitch(QBittorrentPlusTorrentEntity, SwitchEntity):
    """Pause/resume a single active torrent. On = running (not paused)."""

    _attr_translation_key = "torrent_running"

    def __init__(
        self,
        coordinator: QBittorrentPlusCoordinator,
        torrent_hash: str,
        name: str,
    ) -> None:
        super().__init__(coordinator, torrent_hash, "running", name)

    @property
    def is_on(self) -> bool:
        """True when torrent is not paused/stopped."""
        data = self.torrent_data() or {}
        return str(data.get("state") or "") not in PAUSED_STATES

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Resume torrent."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.resume, self.torrent_hash
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Pause torrent."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.pause, self.torrent_hash
        )
        await self.coordinator.async_request_refresh()
