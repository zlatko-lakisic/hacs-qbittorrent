"""Number entities for qBittorrent Plus."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import UnitOfDataRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import QBittorrentPlusConfigEntry, QBittorrentPlusCoordinator
from .entity import QBittorrentPlusEntity


@dataclass(frozen=True, kw_only=True)
class QBittorrentPlusNumberDescription(NumberEntityDescription):
    """Number entity with get/set callbacks."""

    value_fn: Callable[[QBittorrentPlusCoordinator], float | None]
    set_fn: Callable[[QBittorrentPlusCoordinator, float], Awaitable[None] | None]


async def _set_global_dl(coordinator: QBittorrentPlusCoordinator, value: float) -> None:
    await coordinator.hass.async_add_executor_job(
        coordinator.api.set_download_limit, int(value)
    )


async def _set_global_ul(coordinator: QBittorrentPlusCoordinator, value: float) -> None:
    await coordinator.hass.async_add_executor_job(
        coordinator.api.set_upload_limit, int(value)
    )


async def _set_pref(
    coordinator: QBittorrentPlusCoordinator, key: str, value: float
) -> None:
    await coordinator.hass.async_add_executor_job(
        lambda: coordinator.api.set_preferences(**{key: int(value)})
    )


def _pref(coordinator: QBittorrentPlusCoordinator, key: str) -> float | None:
    prefs = (coordinator.data or {}).get("preferences") or {}
    if key not in prefs:
        return None
    try:
        return float(prefs[key])
    except (TypeError, ValueError):
        return None


def _server_limit(coordinator: QBittorrentPlusCoordinator, key: str) -> float | None:
    server = (coordinator.data or {}).get("server_state") or {}
    try:
        return float(server.get(key) or 0)
    except (TypeError, ValueError):
        return None


NUMBER_TYPES: tuple[QBittorrentPlusNumberDescription, ...] = (
    QBittorrentPlusNumberDescription(
        key="current_download_limit",
        translation_key="current_download_limit",
        mode=NumberMode.BOX,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        native_min_value=0,
        native_max_value=104857600,
        native_step=1024,
        value_fn=lambda c: _server_limit(c, "dl_rate_limit"),
        set_fn=_set_global_dl,
    ),
    QBittorrentPlusNumberDescription(
        key="current_upload_limit",
        translation_key="current_upload_limit",
        mode=NumberMode.BOX,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        native_min_value=0,
        native_max_value=104857600,
        native_step=1024,
        value_fn=lambda c: _server_limit(c, "up_rate_limit"),
        set_fn=_set_global_ul,
    ),
    QBittorrentPlusNumberDescription(
        key="normal_download_limit",
        translation_key="normal_download_limit",
        mode=NumberMode.BOX,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        native_min_value=0,
        native_max_value=104857600,
        native_step=1024,
        entity_registry_enabled_default=False,
        value_fn=lambda c: _pref(c, "dl_limit"),
        set_fn=lambda c, v: _set_pref(c, "dl_limit", v),
    ),
    QBittorrentPlusNumberDescription(
        key="normal_upload_limit",
        translation_key="normal_upload_limit",
        mode=NumberMode.BOX,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        native_min_value=0,
        native_max_value=104857600,
        native_step=1024,
        entity_registry_enabled_default=False,
        value_fn=lambda c: _pref(c, "up_limit"),
        set_fn=lambda c, v: _set_pref(c, "up_limit", v),
    ),
    QBittorrentPlusNumberDescription(
        key="alt_download_limit",
        translation_key="alt_download_limit",
        mode=NumberMode.BOX,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        native_min_value=0,
        native_max_value=104857600,
        native_step=1024,
        entity_registry_enabled_default=False,
        value_fn=lambda c: _pref(c, "alt_dl_limit"),
        set_fn=lambda c, v: _set_pref(c, "alt_dl_limit", v),
    ),
    QBittorrentPlusNumberDescription(
        key="alt_upload_limit",
        translation_key="alt_upload_limit",
        mode=NumberMode.BOX,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        native_min_value=0,
        native_max_value=104857600,
        native_step=1024,
        entity_registry_enabled_default=False,
        value_fn=lambda c: _pref(c, "alt_up_limit"),
        set_fn=lambda c, v: _set_pref(c, "alt_up_limit", v),
    ),
    QBittorrentPlusNumberDescription(
        key="listen_port",
        translation_key="listen_port_number",
        mode=NumberMode.BOX,
        native_min_value=1,
        native_max_value=65535,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        value_fn=lambda c: _pref(c, "listen_port"),
        set_fn=lambda c, v: _set_pref(c, "listen_port", v),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: QBittorrentPlusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        QBittorrentPlusNumber(coordinator, description) for description in NUMBER_TYPES
    )


class QBittorrentPlusNumber(QBittorrentPlusEntity, NumberEntity):
    """Writable number bound to transfer limits / preferences."""

    entity_description: QBittorrentPlusNumberDescription

    def __init__(
        self,
        coordinator: QBittorrentPlusCoordinator,
        description: QBittorrentPlusNumberDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        """Return current value."""
        return self.entity_description.value_fn(self.coordinator)

    async def async_set_native_value(self, value: float) -> None:
        """Write value to qBittorrent."""
        result = self.entity_description.set_fn(self.coordinator, value)
        if result is not None:
            await result
        await self.coordinator.async_request_refresh()
