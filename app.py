#!/usr/bin/env python3
"""
YouTube Downloader - Web App (progress tracking + persistent saved path)

A simple local web app: paste a link, choose video or audio,
watch a live progress bar, and see exactly where the file was saved.

SETUP (run once):
    pip install flask yt-dlp
    # ffmpeg must also be installed and on PATH (see README.md)

RUN:
    python app.py

Then open: http://127.0.0.1:5000 in your browser.

Only download content you have the rights to.
"""

import shutil
import threading
import uuid
from pathlib import Path

from flask import Flask, request, jsonify, send_file, render_template

import yt_dlp

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

TEMP_DIR = BASE_DIR / ".tmp_jobs"
TEMP_DIR.mkdir(exist_ok=True)

# In-memory store of job progress. Fine for a single-user local app.
# jobs[job_id] = {"status": ..., "percent": float, "filename": str|None,
#                  "path": str|None, "error": str|None}
jobs = {}
jobs_lock = threading.Lock()


def make_progress_hook(job_id):
    def hook(d):
        with jobs_lock:
            job = jobs.get(job_id)
            if job is None:
                return
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes", 0)
                if total:
                    job["percent"] = round(downloaded / total * 100, 1)
                job["status"] = "downloading"
            elif d["status"] == "finished":
                # File downloaded, may still need audio conversion/merging
                job["percent"] = 100
                job["status"] = "converting"
    return hook


def unique_destination(filename: str) -> Path:
    """Avoid overwriting an existing file of the same name in DOWNLOAD_DIR."""
    dest = DOWNLOAD_DIR / filename
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    counter = 2
    while True:
        candidate = DOWNLOAD_DIR / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def run_download(job_id, url, mode, quality, job_dir):
    try:
        # Resilience options for very large / long files (multi-hour audio,
        # big video): retry aggressively instead of giving up on a hiccup,
        # and use a generous socket timeout so slow connections don't
        # trigger a premature "read timed out".
        common_opts = {
            "outtmpl": str(job_dir / "%(title)s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "progress_hooks": [make_progress_hook(job_id)],
            "retries": 20,
            "fragment_retries": 20,
            "socket_timeout": 60,
            "continuedl": True,
            "concurrent_fragment_downloads": 4,
        }

        if mode == "audio":
            # High = 320kbps, Medium = 192kbps, Low = 96kbps
            audio_quality = {"high": "320", "medium": "192", "low": "96"}.get(quality, "192")
            ydl_opts = {
                **common_opts,
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": audio_quality,
                    }
                ],
            }
        else:
            # High = best available (no cap), Medium = up to 720p, Low = up to 480p
            # Fall back to "best" at the end so a platform that doesn't offer
            # a stream at exactly this height cap (common on Facebook, etc.)
            # still downloads something instead of failing outright.
            height_cap = {"high": None, "medium": 720, "low": 480}.get(quality)
            if height_cap:
                video_format = f"bv*[height<={height_cap}]+ba/best[height<={height_cap}]/best"
            else:
                video_format = "bv*+ba/best"

            ydl_opts = {
                **common_opts,
                "format": video_format,
                "merge_output_format": "mp4",
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        files = list(job_dir.iterdir())
        if not files:
            raise RuntimeError("Download finished but no file was found.")

        source_file = files[0]
        dest_path = unique_destination(source_file.name)
        shutil.move(str(source_file), str(dest_path))
        job_dir.rmdir()

        with jobs_lock:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["percent"] = 100
            jobs[job_id]["filename"] = dest_path.name
            jobs[job_id]["path"] = str(dest_path.resolve())

    except Exception as e:
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(e)
        shutil.rmtree(job_dir, ignore_errors=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    data = request.get_json(force=True)
    url = (data.get("url") or "").strip()
    mode = data.get("mode", "video")
    quality = data.get("quality", "medium")

    if not url:
        return jsonify({"error": "Please provide a URL."}), 400

    job_id = str(uuid.uuid4())
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    with jobs_lock:
        jobs[job_id] = {
            "status": "starting",
            "percent": 0,
            "filename": None,
            "path": None,
            "error": None,
        }

    thread = threading.Thread(
        target=run_download, args=(job_id, url, mode, quality, job_dir), daemon=True
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/progress/<job_id>")
def progress(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            return jsonify({"error": "Unknown job."}), 404
        return jsonify(job)


@app.route("/file/<job_id>")
def get_file(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None or job["status"] != "done":
            return jsonify({"error": "File not ready."}), 400
        file_path = Path(job["path"])
        filename = job["filename"]

    # Note: the file stays in the downloads/ folder on disk (its path is
    # shown on the page) — this just also hands a copy to the browser.
    return send_file(file_path, as_attachment=True, download_name=filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
