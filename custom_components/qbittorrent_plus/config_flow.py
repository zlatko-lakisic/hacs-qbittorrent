"""Config flow for qBittorrent Plus."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import callback
from .api import (
    QBittorrentPlusApi,
    QBittorrentPlusAuthError,
    QBittorrentPlusConnectionError,
)
from .const import (
    CONF_EXPOSE_ACTIVE_TORRENTS,
    CONF_MAX_TORRENT_ENTITIES,
    CONF_SCAN_INTERVAL,
    CONF_URL,
    DEFAULT_EXPOSE_ACTIVE_TORRENTS,
    DEFAULT_MAX_TORRENT_ENTITIES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)
from .helpers import normalize_url

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Optional(CONF_USERNAME, default=""): str,
        vol.Optional(CONF_PASSWORD, default=""): str,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)


async def _validate_connection(
    hass,
    url: str,
    username: str,
    password: str,
    verify_ssl: bool,
) -> dict[str, str]:
    """Validate credentials; return empty errors dict on success."""
    api = QBittorrentPlusApi(url, username, password, verify_ssl)
    try:
        await hass.async_add_executor_job(api.connect)
    except QBittorrentPlusAuthError:
        return {"base": "invalid_auth"}
    except QBittorrentPlusConnectionError:
        return {"base": "cannot_connect"}
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Unexpected error connecting to qBittorrent at %s", url)
        return {"base": "unknown"}
    return {}


class QBittorrentPlusConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for qBittorrent Plus."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return QBittorrentPlusOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a qBittorrent WebUI instance."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            unique = normalize_url(url)
            await self.async_set_unique_id(unique)
            self._abort_if_unique_id_configured()

            errors = await _validate_connection(
                self.hass,
                url,
                user_input.get(CONF_USERNAME, ""),
                user_input.get(CONF_PASSWORD, ""),
                user_input.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
            )
            if not errors:
                return self.async_create_entry(
                    title="qBittorrent Plus",
                    data={
                        CONF_URL: url,
                        CONF_USERNAME: user_input.get(CONF_USERNAME, ""),
                        CONF_PASSWORD: user_input.get(CONF_PASSWORD, ""),
                        CONF_VERIFY_SSL: user_input.get(
                            CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL
                        ),
                    },
                    options={
                        CONF_EXPOSE_ACTIVE_TORRENTS: DEFAULT_EXPOSE_ACTIVE_TORRENTS,
                        CONF_MAX_TORRENT_ENTITIES: DEFAULT_MAX_TORRENT_ENTITIES,
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class QBittorrentPlusOptionsFlow(OptionsFlow):
    """Handle options for qBittorrent Plus."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage hybrid torrent exposure options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_EXPOSE_ACTIVE_TORRENTS,
                        default=options.get(
                            CONF_EXPOSE_ACTIVE_TORRENTS, DEFAULT_EXPOSE_ACTIVE_TORRENTS
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_MAX_TORRENT_ENTITIES,
                        default=options.get(
                            CONF_MAX_TORRENT_ENTITIES, DEFAULT_MAX_TORRENT_ENTITIES
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=200)),
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                }
            ),
        )
