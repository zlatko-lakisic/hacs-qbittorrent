"""Shared entity helpers for qBittorrent Plus."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import QBittorrentPlusCoordinator


def instance_device_info(coordinator: QBittorrentPlusCoordinator) -> DeviceInfo:
    """Device info for the qBittorrent instance."""
    entry = coordinator.config_entry
    version = None
    if coordinator.data:
        version = coordinator.data.get("app_version")
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title or "qBittorrent Plus",
        manufacturer="qBittorrent",
        model="qBittorrent",
        sw_version=version,
        configuration_url=coordinator.api.url,
        entry_type=DeviceEntryType.SERVICE,
    )


def torrent_device_info(
    coordinator: QBittorrentPlusCoordinator,
    torrent_hash: str,
    name: str,
) -> DeviceInfo:
    """Device info for a dynamic active torrent (via instance device)."""
    entry = coordinator.config_entry
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_{torrent_hash}")},
        name=name,
        manufacturer="qBittorrent",
        model="Torrent",
        via_device=(DOMAIN, entry.entry_id),
        entry_type=DeviceEntryType.SERVICE,
    )


class QBittorrentPlusEntity(CoordinatorEntity[QBittorrentPlusCoordinator]):
    """Base entity bound to the instance device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: QBittorrentPlusCoordinator,
        unique_suffix: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{unique_suffix}"
        self._attr_device_info = instance_device_info(coordinator)


class QBittorrentPlusTorrentEntity(CoordinatorEntity[QBittorrentPlusCoordinator]):
    """Base entity for a dynamic active torrent."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: QBittorrentPlusCoordinator,
        torrent_hash: str,
        unique_suffix: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self.torrent_hash = torrent_hash
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{torrent_hash}_{unique_suffix}"
        )
        self._attr_device_info = torrent_device_info(coordinator, torrent_hash, name)

    @property
    def available(self) -> bool:
        """Available when coordinator is ok and torrent is still selected."""
        if not super().available:
            return False
        return self.torrent_hash in self.coordinator.selected_active_torrents()

    def torrent_data(self) -> dict | None:
        """Return current torrent mapping if present."""
        torrents = (self.coordinator.data or {}).get("torrents") or {}
        return torrents.get(self.torrent_hash)
