import os
import json
import threading
from datetime import datetime

class HistoryManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(HistoryManager, cls).__new__(cls)
                cls._instance.init()
            return cls._instance

    def init(self):
        self.history_file = os.path.join(os.getcwd(), 'history.json')
        self._history_lock = threading.Lock()
        self.history = self._load()

    def _load(self):
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            return []

    def _save(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_entry(self, title, url, file_path=None):
        with self._history_lock:
            entry = {
                'title': title,
                'url': url,
                'file_path': file_path,
                'date': datetime.now().isoformat()
            }
            # Avoid duplicates (if same url, just move to top)
            self.history = [h for h in self.history if h['url'] != url]
            self.history.insert(0, entry)
            self._save()

    def get_history(self):
        with self._history_lock:
            return list(self.history)

    def clear_history(self):
        with self._history_lock:
            self.history = []
            self._save()

history_manager = HistoryManager()
