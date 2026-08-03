"""Unit tests for qBittorrent Plus helpers (no Home Assistant required)."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

PKG_DIR = (
    Path(__file__).resolve().parents[1] / "custom_components" / "qbittorrent_plus"
)


def _load(fullname: str, path: Path):
    spec = importlib.util.spec_from_file_location(fullname, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
    return module


pkg = types.ModuleType("qbittorrent_plus")
pkg.__path__ = [str(PKG_DIR)]  # type: ignore[attr-defined]
sys.modules["qbittorrent_plus"] = pkg
_load("qbittorrent_plus.const", PKG_DIR / "const.py")
helpers = _load("qbittorrent_plus.helpers", PKG_DIR / "helpers.py")

seconds_to_hhmmss = helpers.seconds_to_hhmmss
is_active_torrent = helpers.is_active_torrent
select_active_torrents = helpers.select_active_torrents
derive_counts = helpers.derive_counts
merge_sync_maindata = helpers.merge_sync_maindata
format_torrent = helpers.format_torrent


def test_seconds_to_hhmmss() -> None:
    assert seconds_to_hhmmss(3661) == "01:01:01"
    assert seconds_to_hhmmss(8640000) is None
    assert seconds_to_hhmmss(0) is None


def test_is_active_torrent() -> None:
    assert is_active_torrent({"state": "downloading"})
    assert is_active_torrent({"state": "stalledUP"})
    assert not is_active_torrent({"state": "pausedDL"})
    assert not is_active_torrent({"state": "stoppedUP"})
    assert not is_active_torrent({"state": "error"})


def test_select_active_torrents_cap_and_sort() -> None:
    torrents = {
        "a": {"state": "downloading", "dlspeed": 100, "upspeed": 0, "added_on": 1},
        "b": {"state": "uploading", "dlspeed": 0, "upspeed": 50, "added_on": 9},
        "c": {"state": "pausedDL", "dlspeed": 999, "upspeed": 999, "added_on": 99},
        "d": {"state": "forcedDL", "dlspeed": 200, "upspeed": 10, "added_on": 2},
    }
    selected = select_active_torrents(torrents, max_entities=2)
    assert list(selected.keys()) == ["d", "a"]
    assert "c" not in selected


def test_select_active_torrents_disabled_cap() -> None:
    torrents = {"a": {"state": "downloading", "dlspeed": 1, "upspeed": 0, "added_on": 1}}
    assert select_active_torrents(torrents, max_entities=0) == {}


def test_derive_counts() -> None:
    torrents = {
        "1": {"state": "downloading"},
        "2": {"state": "uploading"},
        "3": {"state": "pausedDL"},
        "4": {"state": "error"},
        "5": {"state": "stalledDL"},
        "6": {"state": "queuedUP"},
    }
    counts = derive_counts(torrents)
    assert counts["all"] == 6
    assert counts["downloading"] == 2
    assert counts["seeding"] == 2
    assert counts["paused"] == 1
    assert counts["errored"] == 1
    assert counts["stalled"] == 1
    assert counts["queued"] == 1
    assert counts["active"] == 4


def test_merge_sync_maindata_full_and_delta() -> None:
    full = {
        "full_update": True,
        "torrents": {
            "h1": {"name": "One", "state": "downloading", "dlspeed": 1},
            "h2": {"name": "Two", "state": "pausedDL", "dlspeed": 0},
        },
    }
    merged = merge_sync_maindata({}, full)
    assert set(merged) == {"h1", "h2"}
    assert merged["h1"]["hash"] == "h1"

    delta = {
        "full_update": False,
        "torrents": {"h1": {"dlspeed": 50}},
        "torrents_removed": ["h2"],
    }
    merged = merge_sync_maindata(merged, delta)
    assert "h2" not in merged
    assert merged["h1"]["name"] == "One"
    assert merged["h1"]["dlspeed"] == 50


def test_format_torrent() -> None:
    formatted = format_torrent(
        {
            "hash": "abc",
            "name": "Test",
            "progress": 0.5,
            "state": "downloading",
            "eta": 120,
            "ratio": 1.234,
            "added_on": 1700000000,
            "category": "tv",
            "tags": "a,b",
            "save_path": "/data",
            "size": 1000,
            "dlspeed": 10,
            "upspeed": 2,
            "num_seeds": 3,
            "num_leechs": 4,
        }
    )
    assert formatted["hash"] == "abc"
    assert formatted["percent_done"] == "50.00"
    assert formatted["progress"] == 50.0
    assert formatted["eta"] == "00:02:00"
    assert formatted["ratio"] == 1.23
    assert formatted["category"] == "tv"


if __name__ == "__main__":
    test_seconds_to_hhmmss()
    test_is_active_torrent()
    test_select_active_torrents_cap_and_sort()
    test_select_active_torrents_disabled_cap()
    test_derive_counts()
    test_merge_sync_maindata_full_and_delta()
    test_format_torrent()
    print("all tests passed")
