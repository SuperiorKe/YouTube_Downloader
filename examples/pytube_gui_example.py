from pytube import YouTube
import re

def clean_url(url):
    # Remove any parameters after '?' in the URL
    base_url = url.split('?')[0]
    # Extract video ID from various YouTube URL formats
    if 'youtu.be' in base_url:
        video_id = base_url.split('/')[-1]
    elif 'youtube.com' in base_url:
        video_id = re.search(r'v=([^&]+)', url).group(1) if 'v=' in url else base_url.split('/')[-1]
    else:
        return url
    # Return clean YouTube URL
    return f'https://www.youtube.com/watch?v={video_id}'

def download_with_session(url):
    try:
        # Clean the URL first
        clean_video_url = clean_url(url)
        print(f"Processing URL: {clean_video_url}")
        
        # Create YouTube object with additional parameters
        yt = YouTube(
            clean_video_url,
            use_oauth=False,
            allow_oauth_cache=False
        )
        
        # Get available streams
        print("Fetching available streams...")
        streams = yt.streams.filter(progressive=True, file_extension='mp4')
        
        if not streams:
            raise Exception("No suitable streams found for this video")
        
        # Get the highest resolution stream
        video = streams.get_highest_resolution()
        
        print(f"Title: {yt.title}")
        print(f"Resolution: {video.resolution}")
        print("Starting download...")
        
        # Download with a custom filename to avoid issues
        video.download()
        print("Download completed!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("If you're still having issues, try these steps:")
        print("1. Check your internet connection")
        print("2. Make sure the video is not private or age-restricted")
        print("3. Try copying the URL directly from YouTube's address bar")

if __name__ == "__main__":
    # Get URL from user input
    video_url = input("Please enter the YouTube video URL: ")
    download_with_session(video_url)
