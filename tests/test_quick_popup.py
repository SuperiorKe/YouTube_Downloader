import sys
import types
import unittest
from unittest.mock import patch


sys.modules.setdefault("customtkinter", types.SimpleNamespace(CTkToplevel=object))
sys.modules.setdefault(
    "yt_dlp",
    types.SimpleNamespace(YoutubeDL=object),
)
sys.modules.setdefault(
    "plyer",
    types.SimpleNamespace(notification=types.SimpleNamespace(notify=lambda **kwargs: None)),
)

from ytdl_app.quick_popup import QuickPopup


class FakeYoutubeDL:
    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def extract_info(self, url, download):
        return {
            "title": "Downloaded Title",
            "requested_downloads": [{"filepath": "/tmp/downloaded-title.mp4"}],
        }


class FakeState:
    def __init__(self):
        self.added = []
        self.finished = []
        self.errors = []

    def add_download(self, url, title):
        self.added.append((url, title))

    def update_progress(self, url, status):
        pass

    def mark_finished(self, url, file_path):
        self.finished.append((url, file_path))

    def mark_error(self, url):
        self.errors.append(url)


class QuickPopupDownloadTests(unittest.TestCase):
    def test_run_download_uses_cached_title_not_destroyed_label(self):
        popup = QuickPopup.__new__(QuickPopup)
        popup.label = types.SimpleNamespace(
            cget=lambda option: (_ for _ in ()).throw(
                AssertionError("destroyed Tk widget should not be read")
            )
        )

        fake_state = FakeState()

        with (
            patch("ytdl_app.quick_popup.load_config", return_value=object()),
            patch("ytdl_app.quick_popup.build_yt_dlp_options", return_value={"outtmpl": "%(title)s.%(ext)s"}),
            patch("ytdl_app.quick_popup.YoutubeDL", FakeYoutubeDL),
            patch("ytdl_app.quick_popup.show_notification"),
            patch("ytdl_app.state_manager.state", fake_state),
        ):
            popup._run_download("video", "https://youtu.be/example", "Cached Title")

        self.assertEqual(fake_state.added, [("https://youtu.be/example", "Cached Title")])
        self.assertEqual(
            fake_state.finished,
            [("https://youtu.be/example", "/tmp/downloaded-title.mp4")],
        )
        self.assertEqual(fake_state.errors, [])


if __name__ == "__main__":
    unittest.main()
