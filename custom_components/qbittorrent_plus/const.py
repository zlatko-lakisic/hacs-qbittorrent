"""Constants for the qBittorrent Plus integration."""

from __future__ import annotations

DOMAIN = "qbittorrent_plus"

CONF_URL = "url"
CONF_VERIFY_SSL = "verify_ssl"
CONF_EXPOSE_ACTIVE_TORRENTS = "expose_active_torrents"
CONF_MAX_TORRENT_ENTITIES = "max_torrent_entities"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_VERIFY_SSL = True
DEFAULT_EXPOSE_ACTIVE_TORRENTS = True
DEFAULT_MAX_TORRENT_ENTITIES = 25
DEFAULT_SCAN_INTERVAL = 30

STATE_UP_DOWN = "up_down"
STATE_SEEDING = "seeding"
STATE_DOWNLOADING = "downloading"
STATE_IDLE = "idle"

# States that qualify a torrent for dynamic entity exposure.
ACTIVE_TORRENT_STATES = frozenset(
    {
        "downloading",
        "metaDL",
        "forcedDL",
        "uploading",
        "forcedUP",
        "stalledDL",
        "stalledUP",
        "checkingDL",
        "checkingUP",
        "moving",
        "queuedDL",
        "queuedUP",
    }
)

PAUSED_STATES = frozenset({"pausedDL", "pausedUP", "stoppedDL", "stoppedUP"})
ERROR_STATES = frozenset({"error", "missingFiles"})
DOWNLOADING_STATES = frozenset(
    {"downloading", "metaDL", "forcedDL", "stalledDL", "queuedDL", "checkingDL"}
)
SEEDING_STATES = frozenset(
    {"uploading", "forcedUP", "stalledUP", "queuedUP", "checkingUP"}
)
STALLED_STATES = frozenset({"stalledDL", "stalledUP"})
QUEUED_STATES = frozenset({"queuedDL", "queuedUP"})
INACTIVE_STATES = frozenset({"stalledDL", "stalledUP"})

SERVICE_GET_TORRENTS = "get_torrents"
SERVICE_GET_TORRENT = "get_torrent"
SERVICE_PAUSE_TORRENTS = "pause_torrents"
SERVICE_RESUME_TORRENTS = "resume_torrents"
SERVICE_DELETE_TORRENTS = "delete_torrents"
SERVICE_RECHECK_TORRENTS = "recheck_torrents"
SERVICE_REANNOUNCE_TORRENTS = "reannounce_torrents"
SERVICE_ADD_TORRENT = "add_torrent"
SERVICE_SET_TORRENT_CATEGORY = "set_torrent_category"
SERVICE_ADD_TORRENT_TAGS = "add_torrent_tags"
SERVICE_REMOVE_TORRENT_TAGS = "remove_torrent_tags"
SERVICE_SET_TORRENT_SHARE_LIMITS = "set_torrent_share_limits"
SERVICE_SET_SPEED_LIMITS = "set_speed_limits"
SERVICE_TOGGLE_ALTERNATIVE_SPEED = "toggle_alternative_speed"
SERVICE_CREATE_CATEGORY = "create_category"
SERVICE_EDIT_CATEGORY = "edit_category"
SERVICE_REMOVE_CATEGORIES = "remove_categories"
SERVICE_CREATE_TAGS = "create_tags"
SERVICE_DELETE_TAGS = "delete_tags"

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_HASHES = "hashes"
ATTR_HASH = "hash"
ATTR_FILTER = "filter"
ATTR_DELETE_FILES = "delete_files"
ATTR_URLS = "urls"
ATTR_TORRENT_FILE = "torrent_file"
ATTR_CATEGORY = "category"
ATTR_SAVE_PATH = "save_path"
ATTR_TAGS = "tags"
ATTR_PAUSED = "paused"
ATTR_RATIO_LIMIT = "ratio_limit"
ATTR_SEEDING_TIME_LIMIT = "seeding_time_limit"
ATTR_DOWNLOAD_LIMIT = "download_limit"
ATTR_UPLOAD_LIMIT = "upload_limit"
ATTR_NAME = "name"
ATTR_SAVEPATH = "savepath"
