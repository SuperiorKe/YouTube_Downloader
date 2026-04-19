import threading
import tkinter as tk
from tkinter import ttk, messagebox

from ytdl_app.downloader import download_single_url, DownloadRequest


class DownloaderGUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("YouTube Downloader")
        self.root.geometry("640x240")

        container = ttk.Frame(self.root, padding=12)
        container.grid(column=0, row=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        ttk.Label(container, text="Video URL").grid(column=0, row=0, sticky="w")
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(container, textvariable=self.url_var, width=80)
        self.url_entry.grid(column=0, row=1, columnspan=3, sticky="ew", pady=(0, 8))

        ttk.Label(container, text="Output Template").grid(column=0, row=2, sticky="w")
        self.template_var = tk.StringVar()
        self.template_entry = ttk.Entry(container, textvariable=self.template_var, width=60)
        self.template_entry.grid(column=0, row=3, sticky="ew", pady=(0, 8))

        ttk.Label(container, text="Download Dir").grid(column=1, row=2, sticky="w")
        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(container, textvariable=self.dir_var, width=40)
        self.dir_entry.grid(column=1, row=3, sticky="ew", padx=(8, 0), pady=(0, 8))

        self.progress_var = tk.StringVar(value="Idle")
        self.progress_label = ttk.Label(container, textvariable=self.progress_var)
        self.progress_label.grid(column=0, row=4, columnspan=3, sticky="w")

        self.download_btn = ttk.Button(container, text="Download", command=self._on_download)
        self.download_btn.grid(column=2, row=3, sticky="e")

        for col in range(3):
            container.columnconfigure(col, weight=1)

    def _on_download(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return

        request = DownloadRequest(
            url=url,
            output_template=self.template_var.get().strip() or None,
            download_dir=self.dir_var.get().strip() or None,
        )

        def on_progress(status):
            if status.get("status") == "downloading":
                self.progress_var.set(status.get("_percent_str", "downloading"))
            elif status.get("status") == "finished":
                self.progress_var.set("Done")

        def worker():
            try:
                download_single_url(url, on_progress=on_progress, request=request)
            except Exception as exc:
                messagebox.showerror("Download failed", str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    DownloaderGUI().run()


if __name__ == "__main__":
    main()


