"""API client wrapper for qBittorrent Plus."""

from __future__ import annotations

from typing import Any

from qbittorrentapi import APIConnectionError, Client, Forbidden403Error, LoginFailed


class QBittorrentPlusAuthError(Exception):
    """Raised when authentication fails."""


class QBittorrentPlusConnectionError(Exception):
    """Raised when the client cannot connect."""


class QBittorrentPlusApi:
    """Thin wrapper around qbittorrent-api Client."""

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
    ) -> None:
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self._client: Client | None = None
        self.app_version: str | None = None
        self.api_version: str | None = None

    @property
    def client(self) -> Client:
        """Return the authenticated client."""
        if self._client is None:
            raise QBittorrentPlusConnectionError("Client is not connected")
        return self._client

    def connect(self) -> None:
        """Create client and log in."""
        try:
            client = Client(
                host=self.url,
                username=self.username or None,
                password=self.password or None,
                VERIFY_WEBUI_CERTIFICATE=self.verify_ssl,
            )
            if self.username or self.password:
                client.auth_log_in(self.username, self.password)
            else:
                client.auth_log_in()
            self._client = client
            self.app_version = str(client.app_version())
            self.api_version = str(client.app_web_api_version())
        except (LoginFailed, Forbidden403Error) as err:
            raise QBittorrentPlusAuthError(str(err)) from err
        except APIConnectionError as err:
            raise QBittorrentPlusConnectionError(str(err)) from err

    def sync_maindata(self, rid: int = 0) -> dict[str, Any]:
        """Fetch sync/maindata."""
        return dict(self.client.sync_maindata(rid=rid))

    def app_preferences(self) -> dict[str, Any]:
        """Fetch application preferences."""
        return dict(self.client.app_preferences())

    def set_preferences(self, **prefs: Any) -> None:
        """Set application preferences."""
        self.client.app_set_preferences(prefs=prefs)

    def transfer_speed_limits_mode(self) -> bool:
        """Return whether alternative speed limits are enabled."""
        return str(self.client.transfer_speed_limits_mode) == "1"

    def toggle_speed_limits_mode(self, intended_state: bool | None = None) -> None:
        """Toggle or set alternative speed limits mode."""
        if intended_state is None:
            self.client.transfer_toggle_speed_limits_mode()
            return
        self.client.transfer_toggle_speed_limits_mode(intended_state)

    def set_download_limit(self, limit: int) -> None:
        """Set global download limit (bytes/s, 0 = unlimited)."""
        self.client.transfer_set_download_limit(limit)

    def set_upload_limit(self, limit: int) -> None:
        """Set global upload limit (bytes/s, 0 = unlimited)."""
        self.client.transfer_set_upload_limit(limit)

    def torrents_info(
        self,
        torrent_filter: str | None = None,
        torrent_hashes: str | None = None,
    ):
        """Fetch torrent info list."""
        kwargs: dict[str, Any] = {}
        if torrent_filter:
            kwargs["status_filter"] = torrent_filter
        if torrent_hashes:
            kwargs["torrent_hashes"] = torrent_hashes
        return self.client.torrents_info(**kwargs)

    def pause(self, hashes: str = "all") -> None:
        """Pause torrents."""
        self.client.torrents_pause(hashes=hashes)

    def resume(self, hashes: str = "all") -> None:
        """Resume torrents."""
        self.client.torrents_resume(hashes=hashes)

    def delete(self, hashes: str, delete_files: bool = False) -> None:
        """Delete torrents."""
        self.client.torrents_delete(delete_files=delete_files, torrent_hashes=hashes)

    def recheck(self, hashes: str) -> None:
        """Recheck torrents."""
        self.client.torrents_recheck(torrent_hashes=hashes)

    def reannounce(self, hashes: str) -> None:
        """Reannounce torrents."""
        self.client.torrents_reannounce(torrent_hashes=hashes)

    def add(
        self,
        urls: str | None = None,
        torrent_files: Any = None,
        category: str | None = None,
        savepath: str | None = None,
        tags: str | None = None,
        is_paused: bool | None = None,
    ) -> None:
        """Add torrents from URLs/magnets and/or torrent files."""
        kwargs: dict[str, Any] = {}
        if category is not None:
            kwargs["category"] = category
        if savepath is not None:
            kwargs["savepath"] = savepath
        if tags is not None:
            kwargs["tags"] = tags
        if is_paused is not None:
            kwargs["is_paused"] = is_paused
        self.client.torrents_add(urls=urls, torrent_files=torrent_files, **kwargs)

    def set_category(self, hashes: str, category: str) -> None:
        """Set torrent category."""
        self.client.torrents_set_category(category=category, torrent_hashes=hashes)

    def add_tags(self, hashes: str, tags: str) -> None:
        """Add tags to torrents."""
        self.client.torrents_add_tags(tags=tags, torrent_hashes=hashes)

    def remove_tags(self, hashes: str, tags: str) -> None:
        """Remove tags from torrents."""
        self.client.torrents_remove_tags(tags=tags, torrent_hashes=hashes)

    def set_share_limits(
        self,
        hashes: str,
        ratio_limit: float,
        seeding_time_limit: int,
    ) -> None:
        """Set share limits for torrents."""
        self.client.torrents_set_share_limits(
            ratio_limit=ratio_limit,
            seeding_time_limit=seeding_time_limit,
            torrent_hashes=hashes,
        )

    def set_torrent_download_limit(self, hashes: str, limit: int) -> None:
        """Set per-torrent download limit."""
        self.client.torrents_set_download_limit(limit=limit, torrent_hashes=hashes)

    def set_torrent_upload_limit(self, hashes: str, limit: int) -> None:
        """Set per-torrent upload limit."""
        self.client.torrents_set_upload_limit(limit=limit, torrent_hashes=hashes)

    def create_category(self, name: str, save_path: str = "") -> None:
        """Create a category."""
        self.client.torrents_create_category(name=name, save_path=save_path)

    def edit_category(self, name: str, save_path: str) -> None:
        """Edit a category."""
        self.client.torrents_edit_category(name=name, save_path=save_path)

    def remove_categories(self, categories: str) -> None:
        """Remove categories."""
        self.client.torrents_remove_categories(categories=categories)

    def create_tags(self, tags: str) -> None:
        """Create tags."""
        self.client.torrents_create_tags(tags=tags)

    def delete_tags(self, tags: str) -> None:
        """Delete tags."""
        self.client.torrents_delete_tags(tags=tags)
