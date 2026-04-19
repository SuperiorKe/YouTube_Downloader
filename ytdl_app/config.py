import os
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any

try:
    # Optional: load .env if present for local dev
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    # dotenv is optional; ignore if not installed
    pass

def get_config_filepath():
    return os.path.join(os.getcwd(), 'config.json')

@dataclass
class AppConfig:
    ffmpeg_path: str | None
    download_dir: str
    output_template: str
    extra_yt_dlp_opts: Dict[str, Any]

def load_config() -> AppConfig:
    config_file = get_config_filepath()
    json_config = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                json_config = json.load(f)
        except Exception as e:
            print(f"Error loading config.json: {e}")

    ffmpeg_path = json_config.get("ffmpeg_path", os.getenv("FFMPEG_PATH"))
    download_dir = json_config.get("download_dir", os.getenv("DOWNLOAD_DIR", os.path.join(os.getcwd(), "downloads")))
    output_template = json_config.get("output_template", os.getenv("OUTPUT_TEMPLATE", "%(title)s.%(ext)s"))

    extra_opts_raw = os.getenv("YTDLP_EXTRA_OPTS", "")
    extra_yt_dlp_opts: Dict[str, Any] = json_config.get("extra_yt_dlp_opts", {})
    
    if extra_opts_raw and not extra_yt_dlp_opts:
        # Fallback to parsing env if nothing in json
        for pair in extra_opts_raw.split(","):
            if "=" in pair:
                key, value = pair.split("=", 1)
                key = key.strip()
                value = value.strip()
                if value.lower() in {"true", "false"}:
                    extra_yt_dlp_opts[key] = value.lower() == "true"
                else:
                    extra_yt_dlp_opts[key] = value

    # Ensure download directory exists
    try:
        os.makedirs(download_dir, exist_ok=True)
    except Exception:
        # Fall back to current working directory if invalid
        download_dir = os.getcwd()

    return AppConfig(
        ffmpeg_path=ffmpeg_path,
        download_dir=download_dir,
        output_template=output_template,
        extra_yt_dlp_opts=extra_yt_dlp_opts,
    )

def save_config(config: AppConfig):
    config_file = get_config_filepath()
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(config), f, indent=4)
    except Exception as e:
        print(f"Error saving config.json: {e}")
