"""Tests for configuration loading and saving."""
import json
import os

from ytdl_app.config import AppConfig, load_config, save_config


def test_load_config_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DOWNLOAD_DIR", raising=False)
    monkeypatch.delenv("OUTPUT_TEMPLATE", raising=False)
    monkeypatch.delenv("FFMPEG_PATH", raising=False)

    config = load_config()

    assert config.output_template == "%(title)s.%(ext)s"
    assert config.download_dir == os.path.join(str(tmp_path), "downloads")
    assert os.path.isdir(config.download_dir)  # created on load


def test_load_config_reads_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"download_dir": str(tmp_path / "vids"), "output_template": "%(id)s.%(ext)s"})
    )

    config = load_config()

    assert config.download_dir == str(tmp_path / "vids")
    assert config.output_template == "%(id)s.%(ext)s"


def test_env_override(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OUTPUT_TEMPLATE", "%(uploader)s.%(ext)s")

    config = load_config()

    assert config.output_template == "%(uploader)s.%(ext)s"


def test_save_and_reload_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = AppConfig(
        ffmpeg_path=None,
        download_dir=str(tmp_path / "out"),
        output_template="%(title)s.%(ext)s",
        extra_yt_dlp_opts={"noplaylist": True},
    )

    save_config(cfg)
    reloaded = load_config()

    assert reloaded.download_dir == str(tmp_path / "out")
    assert reloaded.extra_yt_dlp_opts == {"noplaylist": True}
