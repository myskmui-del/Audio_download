# grab — video & audio downloader

A small local web app: paste a video link, choose video or audio, watch a live progress bar, and get the file — with the exact saved path shown on the page. Built with Flask + [yt-dlp](https://github.com/yt-dlp/yt-dlp).

> **Use responsibly.** Only download content you own or have permission to download. Downloading copyrighted content without permission may violate the source platform's Terms of Service and copyright law. This tool is intended for personal use with content you have rights to (your own uploads, Creative Commons content, or anything the creator/platform explicitly allows).

## Setup

1. **Clone this repo**
   ```bash
   git clone https://github.com/YOUR_USERNAME/grab.git
   cd grab
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install ffmpeg** (required for audio conversion and merging video/audio streams)
   - macOS: `brew install ffmpeg`
   - Windows: `winget install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

## Run

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## How it works

- Paste a link, pick **Video (.mp4)** or **Audio (.mp3)**, choose a quality (**High / Medium / Low**), and click Download.
  - Video: High = best available resolution, Medium = up to 720p, Low = up to 480p.
  - Audio: High = 320 kbps, Medium = 192 kbps, Low = 96 kbps.
- A live progress bar tracks the download percentage; it switches to a "Converting…" animation during the final audio/video processing step (which doesn't report a percentage).
- The finished file is saved permanently to the `downloads/` folder next to `app.py`. Once done, the page shows the exact file path with a **Copy** button, and also hands a copy to your browser's own downloads.
- Built for large files: downloads use aggressive retry settings (20 retries, 60s socket timeout, resumable downloads) so multi-hour audio or large video files can recover from brief connection hiccups instead of failing outright.

## Notes

- This runs **locally only** by default (`127.0.0.1`) — nothing is exposed to the internet unless you explicitly deploy it somewhere.
- Supports YouTube, Facebook, and any other site `yt-dlp` supports.
- Files in `downloads/` are never auto-deleted — clean them up manually when you like.
- If you deploy this publicly for others to use, be aware that many platforms' Terms of Service prohibit third-party downloading tools, and public downloader tools have received takedown requests in the past.

## License

MIT — do what you like, just don't use it to infringe on anyone's rights.
