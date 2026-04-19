import os
import sys
import customtkinter as ctk
from ytdl_app.clipboard_monitor import ClipboardMonitor
from ytdl_app.sys_tray import SysTrayApp
from ytdl_app.quick_popup import QuickPopup
from ytdl_app.dashboard import Dashboard

def main():
    # Initialize the hidden main window for customtkinter
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.withdraw()  # Hide the main window

    # Initialize Dashboard
    dashboard = Dashboard(root)
    dashboard.withdraw() # Hidden by default

    # Function called when a new YouTube URL is copied
    def on_url_detected(url):
        print(f"Detected URL: {url}")
        # Spawn the popup safely in the main GUI thread
        root.after(0, lambda: QuickPopup(root, url))

    # Initialize and start Clipboard Monitor
    clipboard_monitor = ClipboardMonitor(on_url_detected=on_url_detected)
    clipboard_monitor.start()

    # Function to quit the application globally
    def quit_app():
        clipboard_monitor.stop()
        root.quit()
        sys.exit(0)

    def open_dashboard():
        root.after(0, lambda: dashboard.deiconify() or dashboard.focus_force())

    # Initialize and start System Tray icon
    sys_tray = SysTrayApp(on_quit_callback=quit_app, on_open_callback=open_dashboard)
    sys_tray.run() # Starts in background thread

    print("YouTube Downloader Background Service is running.")
    print("Copy a YouTube link to see the magic!")
    
    # Run the main GUI loop (blocking)
    root.mainloop()

if __name__ == "__main__":
    main()
