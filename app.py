import os
import subprocess
import uuid
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

DOWNLOAD_FOLDER = "/tmp/downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    quality = data.get("quality", "720")
    mode = data.get("mode", "video")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    file_id = str(uuid.uuid4())
    output_path = f"{DOWNLOAD_FOLDER}/{file_id}.%(ext)s"

    if mode == "audio":
        command = [
            "yt-dlp",
            "--impersonate", "chrome",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "-o", output_path,
            url
        ]
    else:
        command = [
            "yt-dlp",
            "--impersonate", "chrome",
            "-f", f"bestvideo[height<={quality}][vcodec^=avc][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}]",
            "-o", output_path,
            "--no-playlist",
            url
        ]

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({
                "error": "Download failed",
                "details": result.stderr
            }), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    files_found = os.listdir(DOWNLOAD_FOLDER)
    for f in files_found:
        if f.startswith(file_id):
            return send_file(
                os.path.join(DOWNLOAD_FOLDER, f),
                as_attachment=True
            )

    return jsonify({
        "error": "File not found after download",
        "file_id": file_id,
        "files_in_folder": files_found
    }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
