import customtkinter as ctk
import os
from ytdl_app.state_manager import state
import threading
from ytdl_app.downloader import download_single_url, DownloadRequest
from ytdl_app.notifications import show_notification

class Dashboard(ctk.CTkToplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title("YouTube Downloader Dashboard")
        self.geometry("600x400")
        
        # To avoid being destroyed when user clicks X, we catch the close protocol
        self.protocol("WM_DELETE_WINDOW", self.hide_dashboard)
        
        self.tabview = ctk.CTkTabview(self, command=self._on_tab_change)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_active = self.tabview.add("Active Downloads")
        self.tab_manual = self.tabview.add("Manual Download")
        self.tab_history = self.tabview.add("History")
        self.tab_settings = self.tabview.add("Settings")
        
        self._setup_active_tab()
        self._setup_manual_tab()
        self._setup_history_tab()
        self._setup_settings_tab()
        
        # Register for state updates
        state.register_callback(self.on_state_change)
        
        # Initial draw
        self.on_state_change(state.active_downloads)

    def hide_dashboard(self):
        self.withdraw()

    def _on_tab_change(self):
        if self.tabview.get() == "History":
            self._refresh_history()

    def _setup_active_tab(self):
        self.scroll = ctk.CTkScrollableFrame(self.tab_active)
        self.scroll.pack(fill="both", expand=True)
        self.progress_bars = {} # url -> dict of widgets

    def on_state_change(self, active_downloads):
        # Must run in main thread
        self.after(0, self._render_state, active_downloads)

    def _render_state(self, active_downloads):
        # Remove old ones
        to_remove = []
        for url in self.progress_bars:
            if url not in active_downloads:
                for widget in self.progress_bars[url].values():
                    widget.destroy()
                to_remove.append(url)
        for url in to_remove:
            del self.progress_bars[url]

        # Add or update
        for url, data in active_downloads.items():
            if url not in self.progress_bars:
                # Add new row
                frame = ctk.CTkFrame(self.scroll)
                frame.pack(fill="x", pady=5, padx=5)
                
                title_lbl = ctk.CTkLabel(frame, text=data['title'], anchor="w", font=("Arial", 14, "bold"))
                title_lbl.pack(fill="x", padx=5)
                
                pb = ctk.CTkProgressBar(frame)
                pb.set(0)
                pb.pack(fill="x", padx=5, pady=2)
                
                status_lbl = ctk.CTkLabel(frame, text="", anchor="e", font=("Arial", 11))
                status_lbl.pack(fill="x", padx=5)
                
                self.progress_bars[url] = {
                    'frame': frame,
                    'title_lbl': title_lbl,
                    'pb': pb,
                    'status_lbl': status_lbl
                }
            
            # Update values
            widgets = self.progress_bars[url]
            percent_str = data['percent'].strip('%')
            try:
                percent_float = float(percent_str) / 100.0
            except ValueError:
                percent_float = 0.0
            
            widgets['pb'].set(percent_float)
            if data['status'] == 'finished':
                widgets['status_lbl'].configure(text="Finished")
                widgets['pb'].configure(progress_color="green")
                if 'play_btn' not in widgets and data.get('file_path') and os.path.exists(data['file_path']):
                    play_btn = ctk.CTkButton(widgets['frame'], text="Play", width=60,
                        command=lambda p=data['file_path']: os.system(f'rundll32.exe shell32.dll,OpenAs_RunDLL "{p}"'))
                    play_btn.pack(pady=5)
                    widgets['play_btn'] = play_btn
            else:
                widgets['status_lbl'].configure(text=f"{data['percent']} | {data['speed']} | ETA: {data['eta']}")

    def _setup_manual_tab(self):
        ctk.CTkLabel(self.tab_manual, text="YouTube URL:").pack(anchor="w", pady=(10,0))
        self.url_entry = ctk.CTkEntry(self.tab_manual, width=400)
        self.url_entry.pack(pady=5)
        
        self.format_menu = ctk.CTkOptionMenu(self.tab_manual, values=["Video (High)", "Audio (MP3)"])
        self.format_menu.pack(pady=10)
        
        btn = ctk.CTkButton(self.tab_manual, text="Download Now", command=self._start_manual_download)
        btn.pack(pady=20)

    def _start_manual_download(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        format_type = "audio" if "Audio" in self.format_menu.get() else "video"
        
        self.url_entry.delete(0, 'end')
        self.tabview.set("Active Downloads")
        
        show_notification("Download Started", "Starting manual download...")
        threading.Thread(target=self._run_downloader, args=(url, format_type), daemon=True).start()

    def _run_downloader(self, url, format_type):
        from ytdl_app.downloader import build_yt_dlp_options, load_config
        from yt_dlp import YoutubeDL
        import re
        
        # Attempt to get title first
        title = "Manual Download"
        ydl_opts = {'quiet': True, 'extract_flat': True}
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown Title')
        except:
            pass
            
        state.add_download(url, title)
        
        try:
            config = load_config()
            request = DownloadRequest(url=url)
            opts = build_yt_dlp_options(config, request=request)
            
            def progress_hook(d):
                state.update_progress(url, d)
                
            if "progress_hooks" not in opts:
                opts["progress_hooks"] = []
            opts["progress_hooks"].append(progress_hook)
            
            if format_type == "audio":
                opts["format"] = "bestaudio/best"
                opts["extract_audio"] = True
                opts["audio_format"] = "mp3"
                opts["outtmpl"] = opts["outtmpl"] + ".mp3"
                
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = info.get('requested_downloads', [{'filepath': info.get('_filename')}])[0].get('filepath')
            state.mark_finished(url, file_path)
            show_notification("Download Complete", f"{title} finished.")
        except Exception as e:
            state.mark_error(url)
            show_notification("Download Error", str(e))

    def _setup_settings_tab(self):
        from ytdl_app.config import load_config, save_config
        
        self.config = load_config()
        
        ctk.CTkLabel(self.tab_settings, text="Settings", font=("Arial", 16, "bold")).pack(pady=10)
        
        dir_frame = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        dir_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(dir_frame, text="Download Directory:").pack(anchor="w")
        
        self.dir_entry = ctk.CTkEntry(dir_frame, width=350)
        self.dir_entry.pack(side="left", padx=(0, 10))
        self.dir_entry.insert(0, self.config.download_dir)
        
        def browse_dir():
            d = ctk.filedialog.askdirectory(initialdir=self.config.download_dir)
            if d:
                self.dir_entry.delete(0, 'end')
                self.dir_entry.insert(0, d)
                
        ctk.CTkButton(dir_frame, text="Browse", width=80, command=browse_dir).pack(side="left")
        
        def save_settings():
            self.config.download_dir = self.dir_entry.get().strip()
            save_config(self.config)
            show_notification("Settings Saved", "Preferences have been updated.")
            
        ctk.CTkButton(self.tab_settings, text="Save Settings", command=save_settings).pack(pady=20)

    def _setup_history_tab(self):
        self.history_scroll = ctk.CTkScrollableFrame(self.tab_history)
        self.history_scroll.pack(fill="both", expand=True)
        self.history_widgets = []
        
        btn_refresh = ctk.CTkButton(self.tab_history, text="Refresh History", command=self._refresh_history)
        btn_refresh.pack(pady=5)
        self._refresh_history()

    def _refresh_history(self):
        from ytdl_app.history_manager import history_manager
        # Clear existing
        for w in self.history_widgets:
            w.destroy()
        self.history_widgets.clear()
        
        history = history_manager.get_history()
        if not history:
            lbl = ctk.CTkLabel(self.history_scroll, text="No download history found.")
            lbl.pack(pady=10)
            self.history_widgets.append(lbl)
            return
            
        for item in history:
            frame = ctk.CTkFrame(self.history_scroll)
            frame.pack(fill="x", pady=2, padx=5)
            
            title_lbl = ctk.CTkLabel(frame, text=item['title'], anchor="w", font=("Arial", 12, "bold"))
            title_lbl.pack(fill="x", padx=5, pady=(5,0))
            
            bottom_frame = ctk.CTkFrame(frame, fg_color="transparent")
            bottom_frame.pack(fill="x", padx=5, pady=(0,5))
            
            url_lbl = ctk.CTkLabel(bottom_frame, text=item['url'], anchor="w", font=("Arial", 10), text_color="gray")
            url_lbl.pack(side="left", fill="x", expand=True)

            if item.get('file_path') and os.path.exists(item['file_path']):
                play_btn = ctk.CTkButton(bottom_frame, text="Play", width=60,
                    command=lambda p=item['file_path']: os.system(f'rundll32.exe shell32.dll,OpenAs_RunDLL "{p}"'))
                play_btn.pack(side="right")
            
            self.history_widgets.append(frame)

