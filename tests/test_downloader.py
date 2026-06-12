"""Tests for yt-dlp option building and helpers (no network)."""
import os

from ytdl_app.config import AppConfig
from ytdl_app.downloader import (
    build_format_opts,
    build_yt_dlp_options,
    extract_filepath,
)


def make_config(tmp_path):
    return AppConfig(
        ffmpeg_path=None,
        download_dir=str(tmp_path),
        output_template="%(title)s.%(ext)s",
        extra_yt_dlp_opts={},
    )


def test_video_opts_have_merge_format(tmp_path):
    opts = build_format_opts(make_config(tmp_path), format_type="video")
    assert opts["merge_output_format"] == "mp4"
    assert "postprocessors" not in opts
    expected = os.path.join(str(tmp_path), "%(title)s.%(ext)s")
    assert opts["outtmpl"] == expected


def test_audio_opts_use_extract_audio_postprocessor(tmp_path):
    opts = build_format_opts(make_config(tmp_path), format_type="audio")

    assert opts["format"] == "bestaudio/best"
    # The mp4 merge format must be dropped for audio-only output.
    assert "merge_output_format" not in opts
    assert opts["postprocessors"] == [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
    ]
    # Regression: the template must NOT have ".mp3" appended (caused .webm.mp3).
    assert not opts["outtmpl"].endswith(".mp3")
    assert opts["outtmpl"].endswith("%(title)s.%(ext)s")


def test_extra_opts_override(tmp_path):
    config = make_config(tmp_path)
    config.extra_yt_dlp_opts = {"noplaylist": True}
    opts = build_yt_dlp_options(config)
    assert opts["noplaylist"] is True


def test_progress_hook_wired(tmp_path):
    calls = []
    opts = build_yt_dlp_options(make_config(tmp_path), on_progress=lambda d: calls.append(d))
    assert len(opts["progress_hooks"]) == 1


def test_extract_filepath_prefers_requested_downloads():
    info = {"requested_downloads": [{"filepath": "/tmp/a.mp4"}], "_filename": "/tmp/b.mp4"}
    assert extract_filepath(info) == "/tmp/a.mp4"


def test_extract_filepath_falls_back_to_filename():
    assert extract_filepath({"_filename": "/tmp/b.mp4"}) == "/tmp/b.mp4"
    assert extract_filepath({}) is None
