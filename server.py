import os
import subprocess
import requests
import uuid
import glob
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
            r = requests.get(url, allow_redirects=True, timeout=10)
            url = r.url
        except Exception as e:
            return jsonify({"error": f"Failed to resolve TikTok link: {e}"}), 400

    # Clean old downloads
    for f in glob.glob(os.path.join(DOWNLOADS_FOLDER, "*")):
        os.remove(f)

    # Unique filename to avoid caching and overwriting
    unique_name = str(uuid.uuid4())[:8]
    output_path = os.path.join(DOWNLOADS_FOLDER, f"{unique_name}.mp4")

    # yt-dlp command
    ytdlp_cmd = [
        "yt-dlp",
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "--retries", "5",
        "--embed-metadata",
        "--embed-thumbnail",
        "--add-metadata",
        "-o", output_path,
        url
    ]

    # Optional cookies.txt for restricted videos
    if os.path.exists("cookies.txt"):
        ytdlp_cmd.insert(1, "--cookies")
        ytdlp_cmd.insert(2, "cookies.txt")

    result = subprocess.run(ytdlp_cmd, capture_output=True, text=True)

    if result.returncode != 0 or not os.path.exists(output_path):
        return jsonify({"error": result.stderr}), 500

    return send_file(output_path, as_attachment=True, download_name=f"saverpro_{unique_name}.mp4", mimetype="video/mp4")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
