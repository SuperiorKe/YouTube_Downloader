import threading
import re
from ytdl_app.history_manager import history_manager

class StateManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StateManager, cls).__new__(cls)
                cls._instance.init()
            return cls._instance

    def init(self):
        self.active_downloads = {} # url -> desc, percent string
        self.callbacks = []
        self._state_lock = threading.Lock()

    def register_callback(self, callback):
        with self._state_lock:
            if callback not in self.callbacks:
                self.callbacks.append(callback)

    def unregister_callback(self, callback):
        with self._state_lock:
            if callback in self.callbacks:
                self.callbacks.remove(callback)

    def _notify(self):
        # Callbacks should be fast or thread-safe UI events
        for cb in self.callbacks:
            try:
                cb(self.active_downloads)
            except Exception as e:
                print(f"State callback error: {e}")

    def add_download(self, url, title):
        with self._state_lock:
            self.active_downloads[url] = {
                'title': title,
                'status': 'starting',
                'percent': '0%',
                'speed': '',
                'eta': ''
            }
        self._notify()

    def update_progress(self, url, status_dict):
        def strip_ansi(text):
            if not text:
                return ''
            # Remove ANSI color escape codes like \x1b[0;32m
            return re.sub(r'\x1b\[[0-9;]*m', '', text)

        with self._state_lock:
            if url in self.active_downloads:
                status = status_dict.get('status', '')
                if status == 'downloading':
                    self.active_downloads[url]['status'] = 'downloading'
                    self.active_downloads[url]['percent'] = strip_ansi(status_dict.get('_percent_str', '0%'))
                    self.active_downloads[url]['speed'] = strip_ansi(status_dict.get('_speed_str', ''))
                    self.active_downloads[url]['eta'] = strip_ansi(status_dict.get('_eta_str', ''))
                elif status == 'finished':
                    if self.active_downloads[url]['status'] != 'finished':
                        self.active_downloads[url]['status'] = 'processing'
                        self.active_downloads[url]['percent'] = 'Processing...'
        self._notify()

    def mark_finished(self, url, file_path=None):
        with self._state_lock:
            if url in self.active_downloads:
                if self.active_downloads[url]['status'] != 'finished':
                    self.active_downloads[url]['status'] = 'finished'
                    self.active_downloads[url]['percent'] = '100%'
                    self.active_downloads[url]['file_path'] = file_path
                    history_manager.add_entry(self.active_downloads[url]['title'], url, file_path)
        self._notify()

    def mark_error(self, url):
        with self._state_lock:
            if url in self.active_downloads:
                self.active_downloads[url]['status'] = 'error'
                self.active_downloads[url]['percent'] = 'Error'
        self._notify()

    def remove_download(self, url):
        with self._state_lock:
            if url in self.active_downloads:
                del self.active_downloads[url]
        self._notify()

# Global Singleton instance
state = StateManager()
