import pystray
from PIL import Image, ImageDraw
import threading

def create_image(width, height, color1, color2):
    # Generate a simple icon if we don't have a real .ico file
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2),
        fill=color2)
    dc.rectangle(
        (0, height // 2, width // 2, height),
        fill=color2)
    return image

class SysTrayApp:
    def __init__(self, on_quit_callback, on_open_callback):
        self.on_quit_callback = on_quit_callback
        self.on_open_callback = on_open_callback
        self.icon = None

    def _setup_menu(self):
        return pystray.Menu(
            pystray.MenuItem("YouTube Downloader", lambda: None, enabled=False),
            pystray.MenuItem("Open Dashboard", self.open_dashboard, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit_app)
        )

    def open_dashboard(self, icon, item):
        self.on_open_callback()

    def quit_app(self, icon, item):
        self.icon.stop()
        self.on_quit_callback()

    def run(self):
        # Run pystray in blocking mode on background thread
        def icon_thread():
            image = create_image(64, 64, 'black', 'red')
            self.icon = pystray.Icon("YTDL", image, "YTDL Monitor", menu=self._setup_menu())
            self.icon.run()
        
        # Pystray's Icon.run() is blocking, so run it in a thread unless it's main thread
        threading.Thread(target=icon_thread, daemon=True).start()
