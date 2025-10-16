from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import tempfile
import os

app = Flask(__name__)
CORS(app)

@app.route("/download", methods=["POST"])
def download_video():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # Temporary folder
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "video.mp4")

        # Fix TikTok mobile short URLs
        if "tiktok.com/t/" in url:
            # yt-dlp can handle redirects automatically, no need to modify link
            pass

        ydl_opts = {
            "outtmpl": output_path,
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "quiet": True,
            "noplaylist": True,
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4"
                }
            ],
            "source_address": "0.0.0.0",
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/108.0.0.0 Safari/537.36"
            ),
        }

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Check if file exists and valid
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            return jsonify({"error": "Video download failed"}), 500

        return send_file(
            output_path,
            as_attachment=True,
            download_name="video.mp4",
            mimetype="video/mp4"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
