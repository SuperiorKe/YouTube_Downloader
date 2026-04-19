import time
import threading
import re
import pyperclip

YOUTUBE_REGEX = r'(https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|live/|shorts/)|youtu\.be/)[a-zA-Z0-9_-]+)'

class ClipboardMonitor:
    def __init__(self, on_url_detected, check_interval=1.0):
        self.on_url_detected = on_url_detected
        self.check_interval = check_interval
        self._running = False
        self._thread = None
        self._last_detected = ""

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            print("Clipboard monitor started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            print("Clipboard monitor stopped.")

    def _monitor_loop(self):
        while self._running:
            try:
                # Get current clipboard content
                clipboard_content = pyperclip.paste().strip()
                
                # Check if it's a YouTube URL and it's new
                if clipboard_content != self._last_detected:
                    match = re.search(YOUTUBE_REGEX, clipboard_content)
                    if match:
                        url = match.group(0)
                        self._last_detected = clipboard_content
                        # Trigger the callback safely
                        self.on_url_detected(url)
            except Exception as e:
                print(f"Clipboard monitor error: {e}")
            
            time.sleep(self.check_interval)
