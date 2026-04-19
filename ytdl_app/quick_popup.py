import customtkinter as ctk
import threading
from yt_dlp import YoutubeDL
from ytdl_app.downloader import download_single_url, DownloadRequest, load_config, build_yt_dlp_options
from ytdl_app.notifications import show_notification

class QuickPopup(ctk.CTkToplevel):
    def __init__(self, master, url, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.url = url
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
        try:
            ydl_opts = {'quiet': True, 'extract_flat': True}
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                video_title = info.get('title', 'Unknown Title')
                
            self.after(0, self.update_ui_with_title, video_title)
        except Exception as e:
            self.after(0, self.update_ui_with_error, str(e))

    def update_ui_with_title(self, title):
        self.label.configure(text=f"Download: {title}")
        self.btn_video.configure(state="normal")
        self.btn_audio.configure(state="normal")

    def update_ui_with_error(self, error):
        self.label.configure(text="Title unavailable. Download anyway?")
        self.btn_video.configure(state="normal")
        self.btn_audio.configure(state="normal")

    def start_download(self, format_type):
        show_notification("Download Started", "Downloading in background...")
        self.destroy()
        
        # Run download in a background thread
        threading.Thread(target=self._run_download, args=(format_type,), daemon=True).start()

    def _run_download(self, format_type):
        from ytdl_app.state_manager import state
        try:
            config = load_config()
            request = DownloadRequest(url=self.url)
            
            opts = build_yt_dlp_options(config, request=request)
            
            # Setup StateManager progress hook
            def progress_hook(d):
                state.update_progress(self.url, d)
            
            if "progress_hooks" not in opts:
                opts["progress_hooks"] = []
            opts["progress_hooks"].append(progress_hook)
            
            if format_type == "audio":
                opts["format"] = "bestaudio/best"
                opts["extract_audio"] = True
                opts["audio_format"] = "mp3"
                opts["outtmpl"] = opts["outtmpl"] + ".mp3"
                
            with YoutubeDL(opts) as ydl:
                # Add to state tracking before download starts
                title_label = self.label.cget("text").replace("Download: ", "").replace("Title unavailable. Download anyway?", "Unknown Title")
                state.add_download(self.url, title_label)
                
                info = ydl.extract_info(self.url, download=True)
                title = info.get('title', 'Video')
                file_path = info.get('requested_downloads', [{'filepath': info.get('_filename')}])[0].get('filepath')
                state.mark_finished(self.url, file_path)
                show_notification("Download Complete", f"{title} has finished downloading.")
        except Exception as e:
            state.mark_error(self.url)
            show_notification("Download Error", str(e))
