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
            "--no-playlist",
            "-o", output_path,
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

    for f in os.listdir(DOWNLOAD_FOLDER):
    if f.startswith(file_id):
        full_path = os.path.join(DOWNLOAD_FOLDER, f)
        if os.path.getsize(full_path) == 0:
            return jsonify({"error": "Downloaded file is empty"}), 500
        return send_file(full_path, as_attachment=True)

    return jsonify({"error": "File not found after download"}), 500


@app.route("/transcode", methods=["POST"])
def transcode():
    file_id = str(uuid.uuid4())
    input_path = f"{DOWNLOAD_FOLDER}/{file_id}_input.mp4"
    output_path = f"{DOWNLOAD_FOLDER}/{file_id}_output.mp4"

    # Save the incoming file
    with open(input_path, "wb") as f:
        f.write(request.data)

    # Transcode to H.264 using ffmpeg
    command = [
        "ffmpeg",
        "-i", input_path,
        "-vcodec", "libx264",
        "-acodec", "aac",
        "-strict", "experimental",
        output_path
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({
                "error": "Transcode failed",
                "details": result.stderr
            }), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return send_file(output_path, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
