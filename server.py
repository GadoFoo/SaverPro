import os
import subprocess
import requests
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

    # Resolve TikTok short URLs
    if "tiktok.com/t/" in url:
        try:
            response = requests.get(url, allow_redirects=True, timeout=10)
            url = response.url
        except Exception as e:
            return jsonify({"error": f"Failed to resolve TikTok short link: {e}"}), 400

    # Clean previous downloads
    for f in os.listdir(DOWNLOADS_FOLDER):
        path = os.path.join(DOWNLOADS_FOLDER, f)
        if os.path.isfile(path):
            os.remove(path)

    output_path = os.path.join(DOWNLOADS_FOLDER, "%(title)s.%(ext)s")

    ytdlp_cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "-o", output_path,
        "--retries", "3",
        "--no-warnings",
        "--quiet",
        "--newline",
        "--geo-bypass",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        url
    ]

    if os.path.exists("cookies.txt"):
        ytdlp_cmd.insert(1, "--cookies")
        ytdlp_cmd.insert(2, "cookies.txt")

    print("Running:", " ".join(ytdlp_cmd))
    result = subprocess.run(ytdlp_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return jsonify({"error": result.stderr}), 500

    # Find the newest video file
    files = [f for f in os.listdir(DOWNLOADS_FOLDER) if f.endswith(".mp4")]
    if not files:
        return jsonify({"error": "No video found after download"}), 404

    latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(DOWNLOADS_FOLDER, f)))
    video_path = os.path.join(DOWNLOADS_FOLDER, latest_file)

    return send_file(video_path, as_attachment=True, download_name=latest_file)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
