import os
import subprocess
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import glob

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

    # yt-dlp command
    output_path = os.path.join(DOWNLOADS_FOLDER, "%(title)s.%(ext)s")
    ytdlp_cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "--retries", "3",
        "-o", output_path,
        url
    ]

    if os.path.exists("cookies.txt"):
        ytdlp_cmd.insert(1, "--cookies")
        ytdlp_cmd.insert(2, "cookies.txt")

    # Run yt-dlp
    result = subprocess.run(ytdlp_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return jsonify({"error": result.stderr}), 500

    # Find the downloaded video
    downloaded_files = glob.glob(os.path.join(DOWNLOADS_FOLDER, "*.mp4"))
    if not downloaded_files:
        return jsonify({"error": "No video found after download."}), 404

    latest_video = max(downloaded_files, key=os.path.getctime)
    filename = os.path.basename(latest_video)

    return send_file(latest_video, as_attachment=True, download_name=filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
