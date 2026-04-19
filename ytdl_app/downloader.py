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


