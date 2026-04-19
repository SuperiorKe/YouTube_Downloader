import sys
import logging
from yt_dlp import YoutubeDL
from ytdl_app.downloader import download_single_url, DownloadRequest

if __name__ == "__main__":
    download_single_url("https://www.youtube.com/watch?v=BaW_jenozKc")
