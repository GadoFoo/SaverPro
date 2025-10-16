import os
import subprocess
import requests
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

    # Resolve TikTok short links if used
    if "tiktok.com/t/" in url:
        try:
            r = requests.get(url, allow_redirects=True, timeout=10)
            url = r.url
        except Exception as e:
            return jsonify({"error": f"Failed to resolve TikTok link: {e}"}), 400

    # Unique output filename (prevents overwriting or cache)
    unique_name = f"video_{uuid.uuid4().hex[:8]}"
    output_path = os.path.join(DOWNLOADS_FOLDER, f"{unique_name}.mp4")

    # yt-dlp command to ensure full-length, merged, audio+video output
    ytdlp_cmd = [
        "yt-dlp",
        "-f", "bv*+ba/b",  # best video + best audio
        "--merge-output-format", "mp4",
        "--no-playlist",
        "--add-metadata",
        "--embed-metadata",
        "--retries", "10",
        "--fragment-retries", "10",
        "--buffer-size", "16M",
        "-o", output_path,
        url
    ]

    # Optional cookies.txt for restricted YouTube videos
    if os.path.exists("cookies.txt"):
        ytdlp_cmd.insert(1, "--cookies")
        ytdlp_cmd.insert(2, "cookies.txt")

    result = subprocess.run(ytdlp_cmd, capture_output=True, text=True)

    if result.returncode != 0 or not os.path.exists(output_path):
        return jsonify({"error": f"Download failed: {result.stderr}"}), 500

    # Mobile browsers (especially iPhones) need explicit filename + type
    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"{unique_name}.mp4",
        mimetype="video/mp4",
        conditional=True
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
