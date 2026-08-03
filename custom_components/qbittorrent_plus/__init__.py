"""qBittorrent Plus integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL, Platform
from homeassistant.core import HomeAssistant

from .api import QBittorrentPlusApi
from .const import CONF_URL, DOMAIN
from .coordinator import QBittorrentPlusConfigEntry, QBittorrentPlusCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: QBittorrentPlusConfigEntry) -> bool:
    """Set up qBittorrent Plus from a config entry."""
    api = QBittorrentPlusApi(
        url=entry.data[CONF_URL],
        username=entry.data.get(CONF_USERNAME, ""),
        password=entry.data.get(CONF_PASSWORD, ""),
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, True),
    )
    await hass.async_add_executor_job(api.connect)

    coordinator = QBittorrentPlusCoordinator(hass, api, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_setup_services(hass)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: QBittorrentPlusConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            await async_unload_services(hass)
            hass.data.pop(DOMAIN, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
