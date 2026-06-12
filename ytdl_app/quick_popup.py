import customtkinter as ctk
import threading
from ytdl_app.downloader import fetch_title
from ytdl_app.download_service import run_tracked_download
from ytdl_app.notifications import show_notification

class QuickPopup(ctk.CTkToplevel):
    def __init__(self, master, url, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.url = url
        self.video_title = None
        self.title("Download Detected")

        # Make borderless and position in bottom right
        self.overrideredirect(True)
        self.attributes('-topmost', True)

        window_width = 350
        window_height = 150
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = screen_width - window_width - 20
        y = screen_height - window_height - 60 # Above taskbar
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.label = ctk.CTkLabel(self, text="Fetching video details...", wraplength=300)
        self.label.grid(row=0, column=0, columnspan=2, padx=10, pady=20)

        self.btn_video = ctk.CTkButton(self, text="Video (High)", command=lambda: self.start_download("video"), state="disabled")
        self.btn_video.grid(row=1, column=0, padx=10, pady=10)

        self.btn_audio = ctk.CTkButton(self, text="Audio (MP3)", command=lambda: self.start_download("audio"), state="disabled")
        self.btn_audio.grid(row=1, column=1, padx=10, pady=10)

        self.btn_close = ctk.CTkButton(self, text="X", width=30, fg_color="transparent", hover_color="red", command=self.destroy)
        self.btn_close.place(relx=0.95, rely=0.05, anchor="ne")

        # Start fetching metadata in background
        threading.Thread(target=self.fetch_metadata, daemon=True).start()

    def fetch_metadata(self):
        title = fetch_title(self.url)
        self.after(0, self.update_ui_with_title, title)

    def update_ui_with_title(self, title):
        self.video_title = title
        self.label.configure(text=f"Download: {title}")
        self.btn_video.configure(state="normal")
        self.btn_audio.configure(state="normal")

    def start_download(self, format_type):
        show_notification("Download Started", "Downloading in background...")
        # Capture the title before the widget is destroyed; the download runs
        # on a background thread and must not touch tkinter widgets.
        title = self.video_title
        url = self.url
        self.destroy()

        threading.Thread(
            target=run_tracked_download,
            args=(url, format_type, title),
            daemon=True,
        ).start()
