import sys
import types
import unittest
from unittest.mock import Mock, patch


def install_quick_popup_stubs():
    ctk = types.ModuleType("customtkinter")
    ctk.CTkToplevel = type("CTkToplevel", (), {})
    ctk.CTkLabel = object
    ctk.CTkButton = object
    sys.modules.setdefault("customtkinter", ctk)

    yt_dlp = types.ModuleType("yt_dlp")
    yt_dlp.YoutubeDL = object
    sys.modules.setdefault("yt_dlp", yt_dlp)

    plyer = types.ModuleType("plyer")
    plyer.notification = types.SimpleNamespace(notify=lambda **kwargs: None)
    sys.modules.setdefault("plyer", plyer)


class FakeYoutubeDL:
    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download=False):
        return {
            "title": "Downloaded Title",
            "requested_downloads": [{"filepath": "/tmp/downloaded.mp4"}],
        }


class QuickPopupDownloadTests(unittest.TestCase):
    def test_run_download_uses_stored_title_without_touching_destroyed_label(self):
        install_quick_popup_stubs()
        from ytdl_app.quick_popup import QuickPopup

        popup = QuickPopup.__new__(QuickPopup)
        popup.url = "https://youtu.be/video"
        popup.video_title = "Fetched Title"

        with (
            patch("ytdl_app.quick_popup.load_config", return_value=object()),
            patch("ytdl_app.quick_popup.build_yt_dlp_options", return_value={"outtmpl": "%(title)s.%(ext)s"}),
            patch("ytdl_app.quick_popup.YoutubeDL", FakeYoutubeDL),
            patch("ytdl_app.quick_popup.show_notification"),
            patch("ytdl_app.state_manager.state.add_download") as add_download,
            patch("ytdl_app.state_manager.state.update_progress"),
            patch("ytdl_app.state_manager.state.mark_finished") as mark_finished,
            patch("ytdl_app.state_manager.state.mark_error") as mark_error,
        ):
            popup._run_download("video")

        add_download.assert_called_once_with(popup.url, "Fetched Title")
        mark_finished.assert_called_once_with(popup.url, "/tmp/downloaded.mp4")
        mark_error.assert_not_called()


class StateManagerSnapshotTests(unittest.TestCase):
    def setUp(self):
        from ytdl_app.state_manager import state

        self.state = state
        with self.state._state_lock:
            self.state.active_downloads.clear()
            self.state.callbacks.clear()

    def tearDown(self):
        with self.state._state_lock:
            self.state.active_downloads.clear()
            self.state.callbacks.clear()

    def test_callbacks_receive_detached_snapshot(self):
        snapshots = []
        self.state.register_callback(snapshots.append)

        self.state.add_download("url-1", "Title")
        first_snapshot = snapshots[-1]
        self.state.update_progress(
            "url-1",
            {
                "status": "downloading",
                "_percent_str": "50%",
                "_speed_str": "1MiB/s",
                "_eta_str": "10",
            },
        )

        self.assertEqual(first_snapshot["url-1"]["status"], "starting")
        self.assertEqual(first_snapshot["url-1"]["percent"], "0%")
        self.assertEqual(snapshots[-1]["url-1"]["percent"], "50%")
        self.assertIsNot(first_snapshot["url-1"], snapshots[-1]["url-1"])

    def test_get_active_downloads_returns_detached_snapshot(self):
        self.state.add_download("url-1", "Title")

        snapshot = self.state.get_active_downloads()
        snapshot["url-1"]["status"] = "corrupted"

        self.assertEqual(self.state.get_active_downloads()["url-1"]["status"], "starting")


if __name__ == "__main__":
    unittest.main()
