"""Sensors for qBittorrent Plus."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Mapping, cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfDataRate, UnitOfInformation, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    STATE_DOWNLOADING,
    STATE_IDLE,
    STATE_SEEDING,
    STATE_UP_DOWN,
)
from .coordinator import QBittorrentPlusConfigEntry, QBittorrentPlusCoordinator
from .entity import QBittorrentPlusEntity, QBittorrentPlusTorrentEntity
from .helpers import torrent_display_name
from .torrent import TorrentEntityManager


def _server(coordinator: QBittorrentPlusCoordinator) -> Mapping[str, Any]:
    return cast(Mapping[str, Any], (coordinator.data or {}).get("server_state") or {})


def _counts(coordinator: QBittorrentPlusCoordinator) -> Mapping[str, Any]:
    return cast(Mapping[str, Any], (coordinator.data or {}).get("counts") or {})


def get_status(coordinator: QBittorrentPlusCoordinator) -> str:
    """Derive idle / downloading / seeding / up_down status."""
    server = _server(coordinator)
    upload = int(server.get("up_info_speed") or 0)
    download = int(server.get("dl_info_speed") or 0)
    if upload > 0 and download > 0:
        return STATE_UP_DOWN
    if upload > 0:
        return STATE_SEEDING
    if download > 0:
        return STATE_DOWNLOADING
    return STATE_IDLE


@dataclass(frozen=True, kw_only=True)
class QBittorrentPlusSensorDescription(SensorEntityDescription):
    """Sensor description with value callback."""

    value_fn: Callable[[QBittorrentPlusCoordinator], Any]


INSTANCE_SENSORS: tuple[QBittorrentPlusSensorDescription, ...] = (
    QBittorrentPlusSensorDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=[STATE_IDLE, STATE_UP_DOWN, STATE_SEEDING, STATE_DOWNLOADING],
        value_fn=get_status,
    ),
    QBittorrentPlusSensorDescription(
        key="connection_status",
        translation_key="connection_status",
        device_class=SensorDeviceClass.ENUM,
        options=["connected", "firewalled", "disconnected"],
        value_fn=lambda c: _server(c).get("connection_status"),
    ),
    QBittorrentPlusSensorDescription(
        key="download_speed",
        translation_key="download_speed",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        value_fn=lambda c: int(_server(c).get("dl_info_speed") or 0),
    ),
    QBittorrentPlusSensorDescription(
        key="upload_speed",
        translation_key="upload_speed",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        value_fn=lambda c: int(_server(c).get("up_info_speed") or 0),
    ),
    QBittorrentPlusSensorDescription(
        key="download_speed_limit",
        translation_key="download_speed_limit",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        entity_registry_enabled_default=False,
        value_fn=lambda c: int(_server(c).get("dl_rate_limit") or 0),
    ),
    QBittorrentPlusSensorDescription(
        key="upload_speed_limit",
        translation_key="upload_speed_limit",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        entity_registry_enabled_default=False,
        value_fn=lambda c: int(_server(c).get("up_rate_limit") or 0),
    ),
    QBittorrentPlusSensorDescription(
        key="session_download",
        translation_key="session_download",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        value_fn=lambda c: int(_server(c).get("dl_info_data") or 0) or None,
    ),
    QBittorrentPlusSensorDescription(
        key="session_upload",
        translation_key="session_upload",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        value_fn=lambda c: int(_server(c).get("up_info_data") or 0) or None,
    ),
    QBittorrentPlusSensorDescription(
        key="alltime_download",
        translation_key="alltime_download",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfInformation.TEBIBYTES,
        value_fn=lambda c: int(_server(c).get("alltime_dl") or 0) or None,
    ),
    QBittorrentPlusSensorDescription(
        key="alltime_upload",
        translation_key="alltime_upload",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfInformation.TEBIBYTES,
        value_fn=lambda c: int(_server(c).get("alltime_ul") or 0) or None,
    ),
    QBittorrentPlusSensorDescription(
        key="global_ratio",
        translation_key="global_ratio",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda c: float(_server(c).get("global_ratio") or 0),
    ),
    QBittorrentPlusSensorDescription(
        key="free_space",
        translation_key="free_space",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        value_fn=lambda c: int(_server(c).get("free_space_on_disk") or 0) or None,
    ),
    QBittorrentPlusSensorDescription(
        key="all_torrents",
        translation_key="all_torrents",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: int(_counts(c).get("all") or 0),
    ),
    QBittorrentPlusSensorDescription(
        key="active_torrents",
        translation_key="active_torrents",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: int(_counts(c).get("active") or 0),
    ),
    QBittorrentPlusSensorDescription(
        key="inactive_torrents",
        translation_key="inactive_torrents",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: int(_counts(c).get("inactive") or 0),
    ),
    QBittorrentPlusSensorDescription(
        key="paused_torrents",
        translation_key="paused_torrents",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: int(_counts(c).get("paused") or 0),
    ),
    QBittorrentPlusSensorDescription(
        key="errored_torrents",
        translation_key="errored_torrents",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: int(_counts(c).get("errored") or 0),
    ),
    QBittorrentPlusSensorDescription(
        key="downloading_torrents",
        translation_key="downloading_torrents",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: int(_counts(c).get("downloading") or 0),
    ),
    QBittorrentPlusSensorDescription(
        key="seeding_torrents",
        translation_key="seeding_torrents",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: int(_counts(c).get("seeding") or 0),
    ),
    QBittorrentPlusSensorDescription(
        key="stalled_torrents",
        translation_key="stalled_torrents",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: int(_counts(c).get("stalled") or 0),
    ),
    QBittorrentPlusSensorDescription(
        key="queued_torrents",
        translation_key="queued_torrents",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: int(_counts(c).get("queued") or 0),
    ),
    QBittorrentPlusSensorDescription(
        key="longest_eta",
        translation_key="longest_eta",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda c: (c.data or {}).get("longest_eta"),
    ),
    QBittorrentPlusSensorDescription(
        key="listen_port",
        translation_key="listen_port",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda c: (c.data or {}).get("preferences", {}).get("listen_port"),
    ),
    QBittorrentPlusSensorDescription(
        key="client_version",
        translation_key="client_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda c: (c.data or {}).get("app_version"),
    ),
    QBittorrentPlusSensorDescription(
        key="api_version",
        translation_key="api_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda c: (c.data or {}).get("api_version"),
    ),
)


@dataclass(frozen=True, kw_only=True)
class TorrentSensorDescription(SensorEntityDescription):
    """Per-torrent sensor description."""

    value_fn: Callable[[Mapping[str, Any]], Any]


TORRENT_SENSORS: tuple[TorrentSensorDescription, ...] = (
    TorrentSensorDescription(
        key="state",
        translation_key="torrent_state",
        value_fn=lambda t: t.get("state"),
    ),
    TorrentSensorDescription(
        key="progress",
        translation_key="torrent_progress",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value_fn=lambda t: round(float(t.get("progress") or 0) * 100, 2),
    ),
    TorrentSensorDescription(
        key="download_speed",
        translation_key="torrent_download_speed",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfDataRate.KIBIBYTES_PER_SECOND,
        value_fn=lambda t: int(t.get("dlspeed") or 0),
    ),
    TorrentSensorDescription(
        key="upload_speed",
        translation_key="torrent_upload_speed",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfDataRate.KIBIBYTES_PER_SECOND,
        value_fn=lambda t: int(t.get("upspeed") or 0),
    ),
    TorrentSensorDescription(
        key="ratio",
        translation_key="torrent_ratio",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda t: round(float(t.get("ratio") or 0), 2),
    ),
    TorrentSensorDescription(
        key="eta",
        translation_key="torrent_eta",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda t: (
            int(t["eta"])
            if t.get("eta") is not None and 0 < int(t.get("eta") or 0) < 8640000
            else None
        ),
    ),
    TorrentSensorDescription(
        key="size",
        translation_key="torrent_size",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_display_precision=2,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        value_fn=lambda t: int(t.get("size") or t.get("total_size") or 0) or None,
    ),
    TorrentSensorDescription(
        key="seeds",
        translation_key="torrent_seeds",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda t: int(t.get("num_seeds") or 0),
    ),
    TorrentSensorDescription(
        key="peers",
        translation_key="torrent_peers",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda t: int(t.get("num_leechs") or 0),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: QBittorrentPlusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        QBittorrentPlusSensor(coordinator, description)
        for description in INSTANCE_SENSORS
    )

    manager = TorrentEntityManager(coordinator, async_add_entities)

    def make_entities(torrent_hash: str, torrent: Mapping[str, Any]) -> list:
        name = torrent_display_name(torrent, torrent_hash)
        return [
            QBittorrentPlusTorrentSensor(coordinator, torrent_hash, name, description)
            for description in TORRENT_SENSORS
        ]

    manager.register(DOMAIN, "sensor", make_entities)
    manager.async_sync()
    entry.async_on_unload(coordinator.async_add_listener(manager.async_sync))


class QBittorrentPlusSensor(QBittorrentPlusEntity, SensorEntity):
    """Instance-level sensor."""

    entity_description: QBittorrentPlusSensorDescription

    def __init__(
        self,
        coordinator: QBittorrentPlusCoordinator,
        description: QBittorrentPlusSensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return sensor value."""
        return self.entity_description.value_fn(self.coordinator)


class QBittorrentPlusTorrentSensor(QBittorrentPlusTorrentEntity, SensorEntity):
    """Per-torrent sensor."""

    entity_description: TorrentSensorDescription

    def __init__(
        self,
        coordinator: QBittorrentPlusCoordinator,
        torrent_hash: str,
        name: str,
        description: TorrentSensorDescription,
    ) -> None:
        super().__init__(coordinator, torrent_hash, description.key, name)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return torrent sensor value."""
        data = self.torrent_data()
        if not data:
            return None
        return self.entity_description.value_fn(data)
