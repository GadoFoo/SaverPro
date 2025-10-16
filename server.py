import subprocess
import os
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

    output_path = os.path.join(DOWNLOADS_FOLDER, "%(title)s.%(ext)s")

    # Decide if it's TikTok or YouTube
    ytdlp_cmd = ["yt-dlp", "-f", "best", "-o", output_path, url]

    # Use cookies if they exist
    if os.path.exists("cookies.txt"):
        ytdlp_cmd.insert(1, "--cookies")
        ytdlp_cmd.insert(2, "cookies.txt")

    # TikTok-specific fix
    if "tiktok.com" in url:
        ytdlp_cmd += [
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "--no-check-certificate",
            "--fixup", "never",
            "--merge-output-format", "mp4",
        ]

    result = subprocess.run(ytdlp_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return jsonify({"error": result.stderr}), 500

    # Find downloaded file
    for file in os.listdir(DOWNLOADS_FOLDER):
        if os.path.isfile(os.path.join(DOWNLOADS_FOLDER, file)):
            return send_file(os.path.join(DOWNLOADS_FOLDER, file), as_attachment=True)

    return jsonify({"error": "File not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
