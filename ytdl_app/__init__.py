"""Top-level package for the YouTube Downloader app.

This package provides:
- Configuration loading from environment variables
- A downloader service that wraps yt-dlp with safe defaults
- CLI and GUI entry points
"""

__all__ = [
    "config",
    "downloader",
]


