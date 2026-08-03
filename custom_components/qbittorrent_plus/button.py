"""Buttons for qBittorrent Plus."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any, Mapping

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import QBittorrentPlusConfigEntry, QBittorrentPlusCoordinator
from .entity import QBittorrentPlusEntity, QBittorrentPlusTorrentEntity
from .helpers import torrent_display_name
from .torrent import TorrentEntityManager


@dataclass(frozen=True, kw_only=True)
class QBittorrentPlusButtonDescription(ButtonEntityDescription):
    """Instance button description."""

    press_fn: Callable[[QBittorrentPlusCoordinator], Coroutine[Any, Any, None]]


async def _pause_all(coordinator: QBittorrentPlusCoordinator) -> None:
    await coordinator.hass.async_add_executor_job(coordinator.api.pause, "all")
    await coordinator.async_request_refresh()


async def _resume_all(coordinator: QBittorrentPlusCoordinator) -> None:
    await coordinator.hass.async_add_executor_job(coordinator.api.resume, "all")
    await coordinator.async_request_refresh()


INSTANCE_BUTTONS: tuple[QBittorrentPlusButtonDescription, ...] = (
    QBittorrentPlusButtonDescription(
        key="pause_all",
        translation_key="pause_all",
        press_fn=_pause_all,
    ),
    QBittorrentPlusButtonDescription(
        key="resume_all",
        translation_key="resume_all",
        press_fn=_resume_all,
    ),
)


@dataclass(frozen=True, kw_only=True)
class TorrentButtonDescription(ButtonEntityDescription):
    """Per-torrent button."""

    press_fn: Callable[[QBittorrentPlusCoordinator, str], Coroutine[Any, Any, None]]


async def _recheck(coordinator: QBittorrentPlusCoordinator, hash_: str) -> None:
    await coordinator.hass.async_add_executor_job(coordinator.api.recheck, hash_)
    await coordinator.async_request_refresh()


async def _reannounce(coordinator: QBittorrentPlusCoordinator, hash_: str) -> None:
    await coordinator.hass.async_add_executor_job(coordinator.api.reannounce, hash_)
    await coordinator.async_request_refresh()


async def _delete(coordinator: QBittorrentPlusCoordinator, hash_: str) -> None:
    await coordinator.hass.async_add_executor_job(coordinator.api.delete, hash_, False)
    await coordinator.async_request_refresh()


TORRENT_BUTTONS: tuple[TorrentButtonDescription, ...] = (
    TorrentButtonDescription(
        key="recheck",
        translation_key="torrent_recheck",
        press_fn=_recheck,
    ),
    TorrentButtonDescription(
        key="reannounce",
        translation_key="torrent_reannounce",
        press_fn=_reannounce,
    ),
    TorrentButtonDescription(
        key="delete",
        translation_key="torrent_delete",
        press_fn=_delete,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: QBittorrentPlusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up buttons."""
    coordinator = entry.runtime_data
    async_add_entities(
        QBittorrentPlusButton(coordinator, description)
        for description in INSTANCE_BUTTONS
    )

    manager = TorrentEntityManager(coordinator, async_add_entities)

    def make_entities(torrent_hash: str, torrent: Mapping[str, Any]) -> list:
        name = torrent_display_name(torrent, torrent_hash)
        return [
            QBittorrentPlusTorrentButton(coordinator, torrent_hash, name, description)
            for description in TORRENT_BUTTONS
        ]

    manager.register(DOMAIN, "button", make_entities)
    manager.async_sync()
    entry.async_on_unload(coordinator.async_add_listener(manager.async_sync))


class QBittorrentPlusButton(QBittorrentPlusEntity, ButtonEntity):
    """Instance-level button."""

    entity_description: QBittorrentPlusButtonDescription

    def __init__(
        self,
        coordinator: QBittorrentPlusCoordinator,
        description: QBittorrentPlusButtonDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.entity_description.press_fn(self.coordinator)


class QBittorrentPlusTorrentButton(QBittorrentPlusTorrentEntity, ButtonEntity):
    """Per-torrent action button."""

    entity_description: TorrentButtonDescription

    def __init__(
        self,
        coordinator: QBittorrentPlusCoordinator,
        torrent_hash: str,
        name: str,
        description: TorrentButtonDescription,
    ) -> None:
        super().__init__(coordinator, torrent_hash, description.key, name)
        self.entity_description = description

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.entity_description.press_fn(self.coordinator, self.torrent_hash)
