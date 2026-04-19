# YouTube Downloader

A clean, modular Python application for downloading videos from YouTube using `yt-dlp` and `pytube`. Designed to provide both Command-Line (CLI) and Graphical User Interfaces (GUI) for flexible and fast downloads.

## 📁 Repository Structure

```text
YouTube_Downloader/
├── main.py                  # Primary entry point for executing downloads
├── requirements.txt         # Project dependencies
├── ytdl_app/                # Core application package
│   ├── cli.py               # Command Line Interface logic
│   ├── gui.py               # Graphical User Interface logic
│   ├── config.py            # Configuration settings
│   └── downloader.py        # Core yt-dlp downloading logic
├── downloads/               # Output directory for saved video files
├── examples/                # Example scripts (e.g., pytube GUI fallback)
└── other_projects/          # Unrelated Python mini-projects & utilities
```

## ✨ Features

- **Robust Download Engine:** Powered by `yt-dlp` to fetch the highest quality streams efficiently.
- **Multiple Interfaces:** Includes both GUI and CLI components in the `ytdl_app` package.
- **Clean Architecture:** Modular design ensures easy maintainability and extensibility.

## 🛠️ Prerequisites & Installation

To run this application, it is recommended to use the provided virtual environment (`work_env`) or create a new one.

1. **Clone or Access the repository**
2. **Activate the virtual environment** (if not already active):
    - Windows: `.\work_env\Scripts\Activate.ps1`
    - Unix/macOS: `source work_env/bin/activate`
3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Usage

Execute the primary script to start downloading. The `main.py` script serves as the basic entry point:

```bash
python main.py
```

*Note: Depending on how the application evolves, you can also leverage the built-in CLI and GUI modules located directly in the `ytdl_app` package.*

## 📌 Coming Soon
Additional features and UX refinements are slated to be implemented based on evolving project requirements.
