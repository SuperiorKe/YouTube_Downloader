"""Tests for the YouTube URL detection regex."""
import re

import pytest

from ytdl_app.clipboard_monitor import YOUTUBE_REGEX


@pytest.mark.parametrize(
    "text",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "http://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/abc123XYZ_-",
        "https://www.youtube.com/live/abc123XYZ_-",
        "check this out https://youtu.be/dQw4w9WgXcQ cool",
    ],
)
def test_regex_matches_youtube_urls(text):
    match = re.search(YOUTUBE_REGEX, text)
    assert match is not None


@pytest.mark.parametrize(
    "text",
    [
        "https://vimeo.com/123456",
        "just some random text",
        "https://example.com/watch?v=abc",
        "",
    ],
)
def test_regex_ignores_non_youtube(text):
    assert re.search(YOUTUBE_REGEX, text) is None


def test_regex_extracts_clean_url():
    text = "watch https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s now"
    match = re.search(YOUTUBE_REGEX, text)
    assert match.group(0) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
