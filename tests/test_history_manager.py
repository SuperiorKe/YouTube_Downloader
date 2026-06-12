"""Tests for HistoryManager persistence and de-duplication."""
import json

from ytdl_app.history_manager import history_manager


def _reset_history(tmp_path):
    """Point the global history manager at an isolated temp file."""
    history_manager.history_file = str(tmp_path / "history.json")
    history_manager.history = []
    return history_manager


def test_add_entry_persists_and_orders(tmp_path):
    hm = _reset_history(tmp_path)

    hm.add_entry("First", "https://youtu.be/a", "/tmp/a.mp4")
    hm.add_entry("Second", "https://youtu.be/b", "/tmp/b.mp4")

    history = hm.get_history()
    assert [h["title"] for h in history] == ["Second", "First"]  # newest first

    saved = json.loads((tmp_path / "history.json").read_text())
    assert len(saved) == 2


def test_add_entry_dedupes_by_url(tmp_path):
    hm = _reset_history(tmp_path)

    hm.add_entry("Old title", "https://youtu.be/a", "/tmp/a.mp4")
    hm.add_entry("New title", "https://youtu.be/a", "/tmp/a2.mp4")

    history = hm.get_history()
    assert len(history) == 1
    assert history[0]["title"] == "New title"


def test_clear_history(tmp_path):
    hm = _reset_history(tmp_path)
    hm.add_entry("x", "https://youtu.be/x")
    hm.clear_history()
    assert hm.get_history() == []
