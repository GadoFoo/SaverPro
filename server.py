import os
import subprocess
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import glob
import uuid

app = Flask(__name__)
CORS(app)

DOWNLOADS_FOLDER = "downloads"
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

@app.route("/download", methods=["POST"])
def download_video():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "Missing URL"}), 400

    # Resolve TikTok short links
    if "tiktok.com/t/" in url:
        try:
            r = requests.get(url, allow_redirects=True, timeout=10)
            url = r.url
        except Exception as e:
            return jsonify({"error": f"Failed to resolve TikTok short link: {e}"}), 400

    # Clean old downloads
    files = glob.glob(os.path.join(DOWNLOADS_FOLDER, "*"))
    for f in files:
        os.remove(f)

    # Unique filename (so iPhone doesn’t cache or overwrite)
    output_path = os.path.join(DOWNLOADS_FOLDER, f"video_{uuid.uuid4().hex[:8]}.mp4")

    # yt-dlp command — fixed for full videos + audio on all devices
    ytdlp_cmd = [
        "yt-dlp",
        "-f", "bv*+ba/b",  # best video + audio (merged)
        "--merge-output-format", "mp4",
        "--no-playlist",
        "--retries", "10",
        "--fragment-retries", "10",
        "--buffer-size", "16M",
        "-o", output_path,
        url
    ]

    # Add cookies if available (helps with YouTube age/gated/HD)
    if os.path.exists("cookies.txt"):
        ytdlp_cmd.insert(1, "--cookies")
        ytdlp_cmd.insert(2, "cookies.txt")

    result = subprocess.run(ytdlp_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return jsonify({"error": result.stderr}), 500

    downloaded_files = glob.glob(os.path.join(DOWNLOADS_FOLDER, "*.mp4"))
    if not downloaded_files:
        return jsonify({"error": "No video found after download."}), 404

    latest_video = max(downloaded_files, key=os.path.getctime)
    filename = os.path.basename(latest_video)

    return send_file(latest_video, as_attachment=True, download_name=filename, mimetype="video/mp4")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
