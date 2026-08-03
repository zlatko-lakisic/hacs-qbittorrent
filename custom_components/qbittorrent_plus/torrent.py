"""Dynamic active-torrent entity manager."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import QBittorrentPlusCoordinator

EntityFactory = Callable[[str, Mapping[str, Any]], list]


class TorrentEntityManager:
    """Track and add/remove dynamic entities for active torrents."""

    def __init__(
        self,
        coordinator: QBittorrentPlusCoordinator,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        self.coordinator = coordinator
        self._async_add_entities = async_add_entities
        self._known: set[str] = set()
        self._domain: str | None = None
        self._platform: str | None = None
        self._factory: EntityFactory | None = None

    def register(self, domain: str, platform: str, factory: EntityFactory) -> None:
        """Register how to build entities for newly selected torrents."""
        self._domain = domain
        self._platform = platform
        self._factory = factory

    @callback
    def async_sync(self) -> None:
        """Add entities for newly selected torrents; remove stale ones."""
        if not self._factory or not self._domain or not self._platform:
            return

        selected = self.coordinator.selected_active_torrents()
        selected_hashes = set(selected)

        new_hashes = selected_hashes - self._known
        stale_hashes = self._known - selected_hashes

        entities: list = []
        for hash_ in new_hashes:
            torrent = selected.get(hash_)
            if torrent is None:
                continue
            entities.extend(self._factory(hash_, torrent))

        if entities:
            self._async_add_entities(entities)

        if stale_hashes:
            self._async_remove_hashes(stale_hashes)

        self._known = selected_hashes

    def _async_remove_hashes(self, hashes: set[str]) -> None:
        """Remove entities whose unique_id contains the torrent hash."""
        hass = self.coordinator.hass
        entry_id = self.coordinator.config_entry.entry_id
        registry = er.async_get(hass)
        assert self._domain and self._platform
        for entity_entry in er.async_entries_for_config_entry(registry, entry_id):
            if entity_entry.domain != self._platform:
                continue
            unique_id = entity_entry.unique_id or ""
            for hash_ in hashes:
                marker = f"{entry_id}_{hash_}_"
                if unique_id.startswith(marker):
                    registry.async_remove(entity_entry.entity_id)
                    break
