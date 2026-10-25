'''
Download youtube mp3
'''

import sys
import yt_dlp


def download_youtube_mp3(video_url):
  ydl_opts = {
      'format': 'bestaudio/best',
      'postprocessors': [
          {
              'key': 'FFmpegExtractAudio',
              'preferredcodec': 'mp3',
              'preferredquality': '192',
          }
      ],
      'outtmpl': '%(title)s.%(ext)s',
  }

  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    print('Downloading and converting audio...')
    ydl.download([video_url])
    print('Download complete!')


if __name__ == '__main__':
  if len(sys.argv) < 2:
    print('Usage: python yt_mp3.py "YOUTUBE_URL"')
  else:
    url = sys.argv[1]
    download_youtube_mp3(url)
