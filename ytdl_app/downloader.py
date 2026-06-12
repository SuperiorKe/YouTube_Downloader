from __future__ import annotations

from typing import Callable, Dict, Any, Iterable
from dataclasses import dataclass
import os

from yt_dlp import YoutubeDL

from ytdl_app.config import load_config, AppConfig


ProgressCallback = Callable[[Dict[str, Any]], None]


@dataclass
class DownloadRequest:
    url: str
    output_template: str | None = None
    download_dir: str | None = None


def build_yt_dlp_options(config: AppConfig, on_progress: ProgressCallback | None = None, request: DownloadRequest | None = None) -> Dict[str, Any]:
    output_template = (request.output_template if request and request.output_template else config.output_template)
    download_dir = (request.download_dir if request and request.download_dir else config.download_dir)

    outtmpl = os.path.join(download_dir, output_template)

    opts: Dict[str, Any] = {
        "outtmpl": outtmpl,
        "progress_hooks": [on_progress] if on_progress else [],
        # Reasonable defaults for video+audio natively compatible with mp4
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
    }

    if config.ffmpeg_path:
        opts["ffmpeg_location"] = config.ffmpeg_path

    # Allow user-specified overrides via env
    opts.update(config.extra_yt_dlp_opts)
    return opts


def build_format_opts(
    config: AppConfig,
    format_type: str = "video",
    on_progress: ProgressCallback | None = None,
    request: DownloadRequest | None = None,
) -> Dict[str, Any]:
    """Build yt-dlp options for a given format type ("video" or "audio").

    For audio we let yt-dlp's FFmpegExtractAudio post-processor produce an mp3
    and rely on the "%(ext)s" output template for the final extension. Manually
    appending ".mp3" to the template (the previous approach) produced broken
    names like "title.webm.mp3".
    """
    opts = build_yt_dlp_options(config, on_progress=on_progress, request=request)

    if format_type == "audio":
        opts["format"] = "bestaudio/best"
        # Audio is remuxed to mp3 by ffmpeg; drop any video-only merge setting.
        opts.pop("merge_output_format", None)
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

    return opts


def extract_filepath(info: Dict[str, Any]) -> str | None:
    """Best-effort resolution of the final output path from yt-dlp info."""
    requested = info.get("requested_downloads")
    if requested:
        return requested[0].get("filepath") or requested[0].get("_filename")
    return info.get("_filename")


def fetch_title(url: str) -> str:
    """Fetch a video's title without downloading. Never raises."""
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get("title", "Unknown Title")
    except Exception:
        return "Unknown Title"


def download(
    url: str,
    format_type: str = "video",
    on_progress: ProgressCallback | None = None,
    request: DownloadRequest | None = None,
) -> str | None:
    """Download a single URL and return the resulting file path (if known)."""
    config = load_config()
    opts = build_format_opts(
        config,
        format_type=format_type,
        on_progress=on_progress,
        request=request or DownloadRequest(url=url),
    )
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return extract_filepath(info)


def download_single_url(url: str, on_progress: ProgressCallback | None = None, request: DownloadRequest | None = None) -> None:
    config = load_config()
    opts = build_yt_dlp_options(config, on_progress=on_progress, request=request or DownloadRequest(url=url))
    with YoutubeDL(opts) as ydl:
        ydl.download([url])


def download_many(urls: Iterable[str], on_progress: ProgressCallback | None = None, request: DownloadRequest | None = None) -> None:
    config = load_config()
    opts = build_yt_dlp_options(config, on_progress=on_progress, request=request)
    with YoutubeDL(opts) as ydl:
        ydl.download(list(urls))


