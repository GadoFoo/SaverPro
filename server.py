import os
import subprocess
import requests
import glob
import uuid
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

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

    # Resolve TikTok short links (like https://www.tiktok.com/t/...)
    if "tiktok.com/t/" in url:
        try:
            r = requests.get(url, allow_redirects=True, timeout=10)
            url = r.url
        except Exception as e:
            return jsonify({"error": f"Failed to resolve TikTok short link: {e}"}), 400

    # Clean old downloads
    for f in glob.glob(os.path.join(DOWNLOADS_FOLDER, "*")):
        os.remove(f)

    # Unique filename (to fix mobile download issues and cache)
    unique_name = f"video_{uuid.uuid4().hex[:8]}"
    output_path = os.path.join(DOWNLOADS_FOLDER, f"{unique_name}.mp4")

    # yt-dlp command - handles full videos, Shorts, and audio merging
    ytdlp_cmd = [
        "yt-dlp",
        "-f", "bv*+ba/b",              # best video + best audio fallback
        "--merge-output-format", "mp4",
        "--no-playlist",
        "--retries", "10",
        "--fragment-retries", "10",
        "--buffer-size", "16M",
        "--add-metadata",
        "--embed-metadata",
        "-o", output_path,
        url
    ]

    # Use cookies if available (for age-restricted or region-blocked videos)
    if os.path.exists("cookies.txt"):
        ytdlp_cmd.insert(1, "--cookies")
        ytdlp_cmd.insert(2, "cookies.txt")

    # Run yt-dlp
    result = subprocess.run(ytdlp_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return jsonify({"error": result.stderr}), 500

    # Verify output exists
    downloaded_files = glob.glob(os.path.join(DOWNLOADS_FOLDER, "*.mp4"))
    if not downloaded_files:
        return jsonify({"error": "No video found after download."}), 404

    latest_video = max(downloaded_files, key=os.path.getctime)
    filename = os.path.basename(latest_video)

    # iPhone Safari requires mimetype for video playback
    return send_file(
        latest_video,
        as_attachment=True,
        download_name=filename,
        mimetype="video/mp4",
        conditional=True
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
