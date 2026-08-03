"""Home Assistant services for qBittorrent Plus."""

from __future__ import annotations

import base64
import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, device_registry as dr

from .const import (
    ATTR_CATEGORY,
    ATTR_CONFIG_ENTRY_ID,
    ATTR_DELETE_FILES,
    ATTR_DOWNLOAD_LIMIT,
    ATTR_FILTER,
    ATTR_HASH,
    ATTR_HASHES,
    ATTR_NAME,
    ATTR_PAUSED,
    ATTR_RATIO_LIMIT,
    ATTR_SAVE_PATH,
    ATTR_SAVEPATH,
    ATTR_SEEDING_TIME_LIMIT,
    ATTR_TAGS,
    ATTR_TORRENT_FILE,
    ATTR_UPLOAD_LIMIT,
    ATTR_URLS,
    DOMAIN,
    SERVICE_ADD_TORRENT,
    SERVICE_ADD_TORRENT_TAGS,
    SERVICE_CREATE_CATEGORY,
    SERVICE_CREATE_TAGS,
    SERVICE_DELETE_TAGS,
    SERVICE_DELETE_TORRENTS,
    SERVICE_EDIT_CATEGORY,
    SERVICE_GET_TORRENT,
    SERVICE_GET_TORRENTS,
    SERVICE_PAUSE_TORRENTS,
    SERVICE_REANNOUNCE_TORRENTS,
    SERVICE_RECHECK_TORRENTS,
    SERVICE_REMOVE_CATEGORIES,
    SERVICE_REMOVE_TORRENT_TAGS,
    SERVICE_RESUME_TORRENTS,
    SERVICE_SET_SPEED_LIMITS,
    SERVICE_SET_TORRENT_CATEGORY,
    SERVICE_SET_TORRENT_SHARE_LIMITS,
    SERVICE_TOGGLE_ALTERNATIVE_SPEED,
)
from .coordinator import QBittorrentPlusCoordinator
from .helpers import format_torrent, format_torrents, hashes_csv

_LOGGER = logging.getLogger(__name__)

FILTER_OPTIONS = [
    "all",
    "downloading",
    "seeding",
    "completed",
    "paused",
    "active",
    "inactive",
    "resumed",
    "stalled",
    "stalled_uploading",
    "stalled_downloading",
    "errored",
]


def _get_coordinator(hass: HomeAssistant, call: ServiceCall) -> QBittorrentPlusCoordinator:
    """Resolve coordinator from config_entry_id or device_id."""
    entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
    if not entry_id and "device_id" in call.data:
        device_id = call.data["device_id"]
        if isinstance(device_id, list):
            device_id = device_id[0] if device_id else None
        registry = dr.async_get(hass)
        device = registry.async_get(device_id) if device_id else None
        if device:
            for domain, identifier in device.identifiers:
                if domain != DOMAIN:
                    continue
                for known_id in hass.data.get(DOMAIN, {}):
                    if identifier == known_id or str(identifier).startswith(
                        f"{known_id}_"
                    ):
                        entry_id = known_id
                        break
                if entry_id:
                    break

    coordinators: dict[str, QBittorrentPlusCoordinator] = hass.data.get(DOMAIN, {})
    if not entry_id:
        if len(coordinators) == 1:
            return next(iter(coordinators.values()))
        raise ServiceValidationError(
            "config_entry_id is required when multiple qBittorrent Plus instances are configured"
        )
    coordinator = coordinators.get(entry_id)
    if coordinator is None:
        raise ServiceValidationError(f"Unknown config_entry_id: {entry_id}")
    return coordinator


def _hashes_from_call(call: ServiceCall, allow_all: bool = True) -> str:
    """Build hashes string from service data."""
    if ATTR_HASHES in call.data:
        return hashes_csv(call.data[ATTR_HASHES], default="all" if allow_all else "")
    if ATTR_HASH in call.data:
        return str(call.data[ATTR_HASH])
    if allow_all:
        return "all"
    raise ServiceValidationError("hashes or hash is required")


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register integration services once."""
    if hass.services.has_service(DOMAIN, SERVICE_GET_TORRENTS):
        return

    async def handle_get_torrents(call: ServiceCall) -> dict[str, Any]:
        coordinator = _get_coordinator(hass, call)
        torrent_filter = call.data.get(ATTR_FILTER, "all")
        torrents = await hass.async_add_executor_job(
            coordinator.api.torrents_info, torrent_filter, None
        )
        return {"torrents": format_torrents(torrents)}

    async def handle_get_torrent(call: ServiceCall) -> dict[str, Any]:
        coordinator = _get_coordinator(hass, call)
        hash_ = call.data[ATTR_HASH]
        torrents = await hass.async_add_executor_job(
            coordinator.api.torrents_info, None, hash_
        )
        items = list(torrents) if torrents is not None else []
        if not items:
            # Fall back to coordinator cache
            cached = (coordinator.data or {}).get("torrents", {}).get(hash_)
            if not cached:
                raise HomeAssistantError(f"Torrent not found: {hash_}")
            return {"torrent": format_torrent(cached)}
        return {"torrent": format_torrent(items[0])}

    async def handle_pause(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await hass.async_add_executor_job(coordinator.api.pause, _hashes_from_call(call))
        await coordinator.async_request_refresh()

    async def handle_resume(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await hass.async_add_executor_job(coordinator.api.resume, _hashes_from_call(call))
        await coordinator.async_request_refresh()

    async def handle_delete(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        hashes = _hashes_from_call(call, allow_all=False)
        if not hashes or hashes == "all":
            raise ServiceValidationError("Explicit hashes are required for delete")
        delete_files = bool(call.data.get(ATTR_DELETE_FILES, False))
        await hass.async_add_executor_job(coordinator.api.delete, hashes, delete_files)
        await coordinator.async_request_refresh()

    async def handle_recheck(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await hass.async_add_executor_job(
            coordinator.api.recheck, _hashes_from_call(call, allow_all=False)
        )
        await coordinator.async_request_refresh()

    async def handle_reannounce(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await hass.async_add_executor_job(
            coordinator.api.reannounce, _hashes_from_call(call, allow_all=False)
        )
        await coordinator.async_request_refresh()

    async def handle_add(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        urls = call.data.get(ATTR_URLS)
        torrent_file = call.data.get(ATTR_TORRENT_FILE)
        torrent_files = None
        if torrent_file:
            torrent_files = base64.b64decode(torrent_file)
        if not urls and torrent_files is None:
            raise ServiceValidationError("urls or torrent_file is required")
        await hass.async_add_executor_job(
            lambda: coordinator.api.add(
                urls=urls,
                torrent_files=torrent_files,
                category=call.data.get(ATTR_CATEGORY),
                savepath=call.data.get(ATTR_SAVE_PATH) or call.data.get(ATTR_SAVEPATH),
                tags=call.data.get(ATTR_TAGS),
                is_paused=call.data.get(ATTR_PAUSED),
            )
        )
        await coordinator.async_request_refresh()

    async def handle_set_category(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await hass.async_add_executor_job(
            coordinator.api.set_category,
            _hashes_from_call(call, allow_all=False),
            call.data[ATTR_CATEGORY],
        )
        await coordinator.async_request_refresh()

    async def handle_add_tags(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await hass.async_add_executor_job(
            coordinator.api.add_tags,
            _hashes_from_call(call, allow_all=False),
            call.data[ATTR_TAGS],
        )
        await coordinator.async_request_refresh()

    async def handle_remove_tags(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await hass.async_add_executor_job(
            coordinator.api.remove_tags,
            _hashes_from_call(call, allow_all=False),
            call.data[ATTR_TAGS],
        )
        await coordinator.async_request_refresh()

    async def handle_share_limits(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await hass.async_add_executor_job(
            coordinator.api.set_share_limits,
            _hashes_from_call(call, allow_all=False),
            float(call.data.get(ATTR_RATIO_LIMIT, -1)),
            int(call.data.get(ATTR_SEEDING_TIME_LIMIT, -1)),
        )
        await coordinator.async_request_refresh()

    async def handle_speed_limits(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        hashes = call.data.get(ATTR_HASHES) or call.data.get(ATTR_HASH)
        dl = call.data.get(ATTR_DOWNLOAD_LIMIT)
        ul = call.data.get(ATTR_UPLOAD_LIMIT)
        if hashes:
            hash_str = hashes_csv(hashes, default="")
            if dl is not None:
                await hass.async_add_executor_job(
                    coordinator.api.set_torrent_download_limit, hash_str, int(dl)
                )
            if ul is not None:
                await hass.async_add_executor_job(
                    coordinator.api.set_torrent_upload_limit, hash_str, int(ul)
                )
        else:
            if dl is not None:
                await hass.async_add_executor_job(coordinator.api.set_download_limit, int(dl))
            if ul is not None:
                await hass.async_add_executor_job(coordinator.api.set_upload_limit, int(ul))
        await coordinator.async_request_refresh()

    async def handle_toggle_alt(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await hass.async_add_executor_job(coordinator.api.toggle_speed_limits_mode)
        await coordinator.async_request_refresh()

    async def handle_create_category(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await hass.async_add_executor_job(
            coordinator.api.create_category,
            call.data[ATTR_NAME],
            call.data.get(ATTR_SAVE_PATH, ""),
        )
        await coordinator.async_request_refresh()

    async def handle_edit_category(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await hass.async_add_executor_job(
            coordinator.api.edit_category,
            call.data[ATTR_NAME],
            call.data.get(ATTR_SAVE_PATH, ""),
        )
        await coordinator.async_request_refresh()

    async def handle_remove_categories(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        categories = call.data[ATTR_NAME]
        if isinstance(categories, list):
            categories = "\n".join(categories)
        await hass.async_add_executor_job(coordinator.api.remove_categories, categories)
        await coordinator.async_request_refresh()

    async def handle_create_tags(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        tags = call.data[ATTR_TAGS]
        await hass.async_add_executor_job(coordinator.api.create_tags, tags)
        await coordinator.async_request_refresh()

    async def handle_delete_tags(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        tags = call.data[ATTR_TAGS]
        await hass.async_add_executor_job(coordinator.api.delete_tags, tags)
        await coordinator.async_request_refresh()

    entry_schema = {
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
        vol.Optional("device_id"): vol.Any(cv.string, [cv.string]),
    }
    hashes_schema = {
        **entry_schema,
        vol.Optional(ATTR_HASHES): vol.Any(cv.string, [cv.string]),
        vol.Optional(ATTR_HASH): cv.string,
    }

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_TORRENTS,
        handle_get_torrents,
        schema=vol.Schema(
            {
                **entry_schema,
                vol.Optional(ATTR_FILTER, default="all"): vol.In(FILTER_OPTIONS),
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_TORRENT,
        handle_get_torrent,
        schema=vol.Schema({**entry_schema, vol.Required(ATTR_HASH): cv.string}),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_PAUSE_TORRENTS, handle_pause, schema=vol.Schema(hashes_schema)
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RESUME_TORRENTS, handle_resume, schema=vol.Schema(hashes_schema)
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_TORRENTS,
        handle_delete,
        schema=vol.Schema(
            {
                **hashes_schema,
                vol.Optional(ATTR_DELETE_FILES, default=False): cv.boolean,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RECHECK_TORRENTS, handle_recheck, schema=vol.Schema(hashes_schema)
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REANNOUNCE_TORRENTS,
        handle_reannounce,
        schema=vol.Schema(hashes_schema),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_TORRENT,
        handle_add,
        schema=vol.Schema(
            {
                **entry_schema,
                vol.Optional(ATTR_URLS): cv.string,
                vol.Optional(ATTR_TORRENT_FILE): cv.string,
                vol.Optional(ATTR_CATEGORY): cv.string,
                vol.Optional(ATTR_SAVE_PATH): cv.string,
                vol.Optional(ATTR_SAVEPATH): cv.string,
                vol.Optional(ATTR_TAGS): cv.string,
                vol.Optional(ATTR_PAUSED): cv.boolean,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TORRENT_CATEGORY,
        handle_set_category,
        schema=vol.Schema({**hashes_schema, vol.Required(ATTR_CATEGORY): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_TORRENT_TAGS,
        handle_add_tags,
        schema=vol.Schema({**hashes_schema, vol.Required(ATTR_TAGS): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_TORRENT_TAGS,
        handle_remove_tags,
        schema=vol.Schema({**hashes_schema, vol.Required(ATTR_TAGS): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TORRENT_SHARE_LIMITS,
        handle_share_limits,
        schema=vol.Schema(
            {
                **hashes_schema,
                vol.Optional(ATTR_RATIO_LIMIT, default=-1): vol.Coerce(float),
                vol.Optional(ATTR_SEEDING_TIME_LIMIT, default=-1): vol.Coerce(int),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SPEED_LIMITS,
        handle_speed_limits,
        schema=vol.Schema(
            {
                **hashes_schema,
                vol.Optional(ATTR_DOWNLOAD_LIMIT): vol.Coerce(int),
                vol.Optional(ATTR_UPLOAD_LIMIT): vol.Coerce(int),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_TOGGLE_ALTERNATIVE_SPEED,
        handle_toggle_alt,
        schema=vol.Schema(entry_schema),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_CATEGORY,
        handle_create_category,
        schema=vol.Schema(
            {
                **entry_schema,
                vol.Required(ATTR_NAME): cv.string,
                vol.Optional(ATTR_SAVE_PATH, default=""): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EDIT_CATEGORY,
        handle_edit_category,
        schema=vol.Schema(
            {
                **entry_schema,
                vol.Required(ATTR_NAME): cv.string,
                vol.Optional(ATTR_SAVE_PATH, default=""): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_CATEGORIES,
        handle_remove_categories,
        schema=vol.Schema(
            {
                **entry_schema,
                vol.Required(ATTR_NAME): vol.Any(cv.string, [cv.string]),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_TAGS,
        handle_create_tags,
        schema=vol.Schema({**entry_schema, vol.Required(ATTR_TAGS): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_TAGS,
        handle_delete_tags,
        schema=vol.Schema({**entry_schema, vol.Required(ATTR_TAGS): cv.string}),
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Remove integration services."""
    services = [
        SERVICE_GET_TORRENTS,
        SERVICE_GET_TORRENT,
        SERVICE_PAUSE_TORRENTS,
        SERVICE_RESUME_TORRENTS,
        SERVICE_DELETE_TORRENTS,
        SERVICE_RECHECK_TORRENTS,
        SERVICE_REANNOUNCE_TORRENTS,
        SERVICE_ADD_TORRENT,
        SERVICE_SET_TORRENT_CATEGORY,
        SERVICE_ADD_TORRENT_TAGS,
        SERVICE_REMOVE_TORRENT_TAGS,
        SERVICE_SET_TORRENT_SHARE_LIMITS,
        SERVICE_SET_SPEED_LIMITS,
        SERVICE_TOGGLE_ALTERNATIVE_SPEED,
        SERVICE_CREATE_CATEGORY,
        SERVICE_EDIT_CATEGORY,
        SERVICE_REMOVE_CATEGORIES,
        SERVICE_CREATE_TAGS,
        SERVICE_DELETE_TAGS,
    ]
    for service in services:
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
