"""Tests for the StateManager download lifecycle and callbacks."""
import pytest

from ytdl_app.state_manager import state
from ytdl_app.history_manager import history_manager


@pytest.fixture(autouse=True)
def clean_state(tmp_path):
    # Isolate history side effects and start from a clean slate each test.
    history_manager.history_file = str(tmp_path / "history.json")
    history_manager.history = []
    for url in list(state.active_downloads.keys()):
        state.remove_download(url)
    state.callbacks.clear()
    yield
    for url in list(state.active_downloads.keys()):
        state.remove_download(url)
    state.callbacks.clear()


URL = "https://youtu.be/abc"


def test_add_download_creates_entry():
    state.add_download(URL, "My Video")
    entry = state.active_downloads[URL]
    assert entry["title"] == "My Video"
    assert entry["status"] == "starting"
    assert entry["percent"] == "0%"


def test_update_progress_strips_ansi():
    state.add_download(URL, "My Video")
    state.update_progress(URL, {
        "status": "downloading",
        "_percent_str": "\x1b[0;32m 50.0%\x1b[0m",
        "_speed_str": "1.2MiB/s",
        "_eta_str": "00:10",
    })
    entry = state.active_downloads[URL]
    assert entry["status"] == "downloading"
    assert entry["percent"] == " 50.0%"  # ANSI codes removed
    assert entry["speed"] == "1.2MiB/s"


def test_mark_finished_records_history():
    state.add_download(URL, "My Video")
    state.mark_finished(URL, "/tmp/v.mp4")
    assert state.active_downloads[URL]["status"] == "finished"
    assert state.active_downloads[URL]["percent"] == "100%"
    assert history_manager.get_history()[0]["url"] == URL


def test_mark_error():
    state.add_download(URL, "My Video")
    state.mark_error(URL)
    assert state.active_downloads[URL]["status"] == "error"


def test_callbacks_are_notified():
    received = []
    state.register_callback(lambda downloads: received.append(dict(downloads)))
    state.add_download(URL, "My Video")
    assert received  # callback fired at least once
    assert URL in received[-1]
