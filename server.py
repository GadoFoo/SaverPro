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

    # Handle TikTok short links like https://www.tiktok.com/t/...
    if "tiktok.com/t/" in url:
        try:
            print("Resolving TikTok short link...")
            response = requests.get(url, allow_redirects=True, timeout=10)
            url = response.url  # real video URL
            print(f"Resolved TikTok URL: {url}")
        except Exception as e:
            return jsonify({"error": f"Failed to resolve TikTok short link: {e}"}), 400

    output_path = os.path.join(DOWNLOADS_FOLDER, "%(title)s.%(ext)s")

    # Base yt-dlp command
    ytdlp_cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", output_path,
        url
    ]

    # Add cookies if available
    if os.path.exists("cookies.txt"):
        ytdlp_cmd.insert(1, "--cookies")
        ytdlp_cmd.insert(2, "cookies.txt")

    # TikTok fixes
    if "tiktok.com" in url:
        ytdlp_cmd += [
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "--no-check-certificate",
            "--fixup", "never"
        ]

    print("Running:", " ".join(ytdlp_cmd))
    result = subprocess.run(ytdlp_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return jsonify({"error": result.stderr}), 500

    # Send downloaded file back
    files = [f for f in os.listdir(DOWNLOADS_FOLDER) if os.path.isfile(os.path.join(DOWNLOADS_FOLDER, f))]
    if files:
        latest = max(files, key=lambda f: os.path.getctime(os.path.join(DOWNLOADS_FOLDER, f)))
        return send_file(os.path.join(DOWNLOADS_FOLDER, latest), as_attachment=True)

    return jsonify({"error": "No file found after download."}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
