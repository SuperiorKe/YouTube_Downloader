from plyer import notification

def show_notification(title, message):
    try:
        notification.notify(
            title=title,
            message=message,
            app_name='YouTube Downloader',
            timeout=5
        )
    except Exception as e:
        print(f"Failed to show notification: {e}")
