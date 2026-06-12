# YouTube Downloader

A desktop YouTube downloader built on [`yt-dlp`](https://github.com/yt-dlp/yt-dlp).
It runs as a lightweight background service that **watches your clipboard** for
YouTube links and offers a one-click download — plus a full dashboard, a system
tray icon, and a command-line interface for scripted use.

## ✨ Features

- **Clipboard auto-detect** — copy any YouTube URL (`watch`, `youtu.be`,
  `shorts`, `live`) and a quick popup appears offering **Video** or **Audio (MP3)**.
- **System tray** — runs quietly in the background; open the dashboard or quit
  from the tray menu.
- **Dashboard** with tabs for:
  - **Active Downloads** — live progress bars, speed and ETA.
  - **Manual Download** — paste a URL and pick a format.
  - **History** — past downloads with a cross-platform **Play** button.
  - **Settings** — change the download directory.
- **Robust engine** — `yt-dlp` fetches the best video+audio and merges to MP4;
  audio downloads are converted to MP3 via ffmpeg.
- **Cross-platform** — Windows, macOS and Linux.

## 📁 Repository Structure

```text
YouTube_Downloader/
├── main.py                     # Entry point: clipboard monitor + tray + dashboard
├── requirements.txt            # Runtime dependencies
├── requirements-dev.txt        # Test dependencies
├── pytest.ini                  # Test configuration
├── ytdl_app/                   # Core application package
│   ├── clipboard_monitor.py    # Watches the clipboard for YouTube URLs
│   ├── quick_popup.py          # The "Download detected" popup
│   ├── dashboard.py            # Tabbed dashboard window
│   ├── sys_tray.py             # System tray icon + menu
│   ├── downloader.py           # yt-dlp option building + download helpers
│   ├── download_service.py     # Shared, UI-agnostic download orchestration
│   ├── state_manager.py        # In-memory active-download state (singleton)
│   ├── history_manager.py      # Persistent download history (history.json)
│   ├── config.py               # Config loading/saving (config.json + env)
│   ├── notifications.py        # Desktop notifications
│   ├── platform_utils.py       # Cross-platform "open file" helper
│   ├── cli.py                  # Command-line interface
│   └── gui.py                  # Minimal standalone Tk GUI
└── tests/                      # Pytest suite
```

## 🛠️ Prerequisites & Installation

- **Python 3.10+**
- **[ffmpeg](https://ffmpeg.org/)** on your `PATH` (required to merge video+audio
  and to produce MP3 audio). Alternatively set `FFMPEG_PATH` (see Configuration).

```bash
# (optional) create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## 🚀 Usage

### Background service (clipboard monitor + tray)

```bash
python main.py
```

Copy a YouTube link anywhere and pick **Video** or **Audio (MP3)** in the popup.
Open the dashboard from the tray icon to watch progress or manage history.

### Command line

```bash
python -m ytdl_app.cli "https://youtu.be/dQw4w9WgXcQ" --dir ./downloads
```

| Option       | Description                                            |
|--------------|--------------------------------------------------------|
| `--dir`      | Download directory (overrides `DOWNLOAD_DIR`).         |
| `--template` | Output template, e.g. `'%(title)s.%(ext)s'`.           |

### Standalone GUI

```bash
python -m ytdl_app.gui
```

## ⚙️ Configuration

Settings are read from `config.json` (in the working directory) and/or
environment variables. JSON values take precedence; a `.env` file is loaded
automatically if present.

| Setting           | `config.json` key   | Env var            | Default                     |
|-------------------|---------------------|--------------------|-----------------------------|
| Download directory| `download_dir`      | `DOWNLOAD_DIR`     | `./downloads`               |
| Output template   | `output_template`   | `OUTPUT_TEMPLATE`  | `%(title)s.%(ext)s`         |
| ffmpeg location   | `ffmpeg_path`       | `FFMPEG_PATH`      | (auto-detected on `PATH`)   |
| Extra yt-dlp opts | `extra_yt_dlp_opts` | `YTDLP_EXTRA_OPTS` | `{}`                        |

`YTDLP_EXTRA_OPTS` accepts comma-separated `key=value` pairs, e.g.
`YTDLP_EXTRA_OPTS="noplaylist=true"`.

## 🧪 Development & Testing

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

The test suite covers the non-GUI logic (option building, config, state, history
and URL detection) and runs in CI on every push and pull request across Python
3.10–3.12. See `.github/workflows/ci.yml`.
