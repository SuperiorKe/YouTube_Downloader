import unittest
from unittest.mock import patch

from ytdl_app import quick_popup


class ImmediateThread:
    def __init__(self, target, args=(), kwargs=None, daemon=None):
        self.target = target
        self.args = args
        self.kwargs = kwargs or {}
        self.daemon = daemon

    def start(self):
        self.target(*self.args, **self.kwargs)


class FakeLabel:
    def __init__(self, text):
        self.text = text
        self.destroyed = False

    def cget(self, option):
        if self.destroyed:
            raise RuntimeError("label was read after popup destruction")
        if option != "text":
            raise ValueError(option)
        return self.text


class QuickPopupStartDownloadTests(unittest.TestCase):
    def make_popup(self, label_text):
        popup = quick_popup.QuickPopup.__new__(quick_popup.QuickPopup)
        popup.label = FakeLabel(label_text)
        popup.started_args = None

        def destroy():
            popup.label.destroyed = True

        def run_download(*args):
            popup.started_args = args

        popup.destroy = destroy
        popup._run_download = run_download
        return popup

    def test_start_download_passes_title_to_worker_before_destroying_popup(self):
        popup = self.make_popup("Download: Example Video")

        with patch.object(quick_popup, "show_notification"), patch.object(quick_popup.threading, "Thread", ImmediateThread):
            popup.start_download("video")

        self.assertTrue(popup.label.destroyed)
        self.assertEqual(popup.started_args, ("video", "Example Video"))

    def test_start_download_uses_unknown_title_when_metadata_failed(self):
        popup = self.make_popup("Title unavailable. Download anyway?")

        with patch.object(quick_popup, "show_notification"), patch.object(quick_popup.threading, "Thread", ImmediateThread):
            popup.start_download("audio")

        self.assertEqual(popup.started_args, ("audio", "Unknown Title"))


if __name__ == "__main__":
    unittest.main()
