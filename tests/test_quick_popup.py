import importlib
import sys
import types
import unittest
from unittest.mock import patch


def install_dependency_stubs():
    if "customtkinter" not in sys.modules:
        customtkinter = types.ModuleType("customtkinter")
        customtkinter.CTkToplevel = type("CTkToplevel", (), {})
        customtkinter.CTkLabel = type("CTkLabel", (), {})
        customtkinter.CTkButton = type("CTkButton", (), {})
        sys.modules["customtkinter"] = customtkinter

    if "yt_dlp" not in sys.modules:
        yt_dlp = types.ModuleType("yt_dlp")
        yt_dlp.YoutubeDL = object
        sys.modules["yt_dlp"] = yt_dlp

    if "plyer" not in sys.modules:
        plyer = types.ModuleType("plyer")
        plyer.notification = types.SimpleNamespace(notify=lambda **kwargs: None)
        sys.modules["plyer"] = plyer


install_dependency_stubs()
quick_popup = importlib.import_module("ytdl_app.quick_popup")


class FakeState:
    def __init__(self):
        self.added = []
        self.finished = []
        self.errors = []
        self.progress = []

    def add_download(self, url, title):
        self.added.append((url, title))

    def update_progress(self, url, status):
        self.progress.append((url, status))

    def mark_finished(self, url, file_path=None):
        self.finished.append((url, file_path))

    def mark_error(self, url):
        self.errors.append(url)


class QuickPopupDownloadTests(unittest.TestCase):
    def test_start_download_passes_cached_title_to_worker_after_destroy(self):
        captured = {}

        class FakeThread:
            def __init__(self, target, args, daemon):
                captured["target"] = target
                captured["args"] = args
                captured["daemon"] = daemon

            def start(self):
                captured["started"] = True

        popup = object.__new__(quick_popup.QuickPopup)
        popup.download_title = "Cached Video Title"
        popup.destroy = lambda: captured.__setitem__("destroyed", True)

        with patch.object(quick_popup, "show_notification"), patch.object(quick_popup.threading, "Thread", FakeThread):
            popup.start_download("video")

        self.assertTrue(captured["destroyed"])
        self.assertTrue(captured["started"])
        self.assertTrue(captured["daemon"])
        self.assertEqual(captured["args"], ("video", "Cached Video Title"))

    def test_worker_uses_title_argument_instead_of_destroyed_widget(self):
        fake_state = FakeState()
        captured = {}

        class ExplodingLabel:
            def cget(self, key):
                raise AssertionError("worker must not read destroyed Tk widgets")

        class FakeYoutubeDL:
            def __init__(self, opts):
                captured["opts"] = opts

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def extract_info(self, url, download):
                captured["extract_info"] = (url, download)
                return {
                    "title": "Downloaded Title",
                    "requested_downloads": [{"filepath": "/tmp/video.mp4"}],
                }

        popup = object.__new__(quick_popup.QuickPopup)
        popup.url = "https://youtu.be/example"
        popup.label = ExplodingLabel()

        with (
            patch.object(quick_popup, "load_config", return_value=object()),
            patch.object(quick_popup, "build_yt_dlp_options", return_value={"progress_hooks": []}),
            patch.object(quick_popup, "YoutubeDL", FakeYoutubeDL),
            patch.object(quick_popup, "show_notification"),
            patch("ytdl_app.state_manager.state", fake_state),
        ):
            popup._run_download("video", "Cached Video Title")

        self.assertEqual(fake_state.added, [("https://youtu.be/example", "Cached Video Title")])
        self.assertEqual(fake_state.finished, [("https://youtu.be/example", "/tmp/video.mp4")])
        self.assertEqual(fake_state.errors, [])
        self.assertEqual(captured["extract_info"], ("https://youtu.be/example", True))


if __name__ == "__main__":
    unittest.main()
