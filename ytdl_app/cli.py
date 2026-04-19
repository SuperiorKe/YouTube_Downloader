import argparse
from ytdl_app.downloader import download_single_url, DownloadRequest


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a single YouTube URL using yt-dlp")
    parser.add_argument("url", help="YouTube video or playlist URL")
    parser.add_argument("--dir", dest="download_dir", default=None, help="Download directory (overrides DOWNLOAD_DIR)")
    parser.add_argument("--template", dest="output_template", default=None, help="Output template, e.g. '%%(title)s.%%(ext)s'")

    args = parser.parse_args()

    request = DownloadRequest(
        url=args.url,
        output_template=args.output_template,
        download_dir=args.download_dir,
    )

    def on_progress(status):  # minimal console progress
        if status.get("status") == "downloading":
            eta = status.get("eta")
            speed = status.get("speed")
            percent = status.get("_percent_str")
            print(f"Downloading {percent} | ETA: {eta}s | Speed: {speed}", end="\r")
        elif status.get("status") == "finished":
            print(f"\nDone: {status.get('filename')}")

    download_single_url(args.url, on_progress=on_progress, request=request)


if __name__ == "__main__":
    main()


