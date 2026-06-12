"""High-level, UI-agnostic download orchestration.

Both the quick popup and the dashboard previously carried near-identical copies
of this flow (fetch title -> register in state -> download with progress hook ->
mark finished/error -> notify). It now lives here once.
"""
from __future__ import annotations

from ytdl_app.downloader import download, fetch_title
from ytdl_app.notifications import show_notification
from ytdl_app.state_manager import state


def run_tracked_download(url: str, format_type: str = "video", title: str | None = None) -> None:
    """Download `url`, reporting progress and results through the shared state
    manager and desktop notifications.

    Intended to be run on a background thread. Never raises; failures are
    surfaced via state + notification.
    """
    if not title:
        title = fetch_title(url)

    state.add_download(url, title)

    def on_progress(status: dict) -> None:
        state.update_progress(url, status)

    try:
        file_path = download(url, format_type=format_type, on_progress=on_progress)
        state.mark_finished(url, file_path)
        show_notification("Download Complete", f"{title} has finished downloading.")
    except Exception as exc:
        state.mark_error(url)
        show_notification("Download Error", str(exc))
