from flask import Flask, request, jsonify, send_file, render_template_string
from yt_dlp import YoutubeDL
import os

import yt_dlp

def download_video(url):
    ydl_opts = {
        'cookies_from_browser': 'chrome',  # 'firefox' für Firefox
        'outtmpl': '%(title)s.%(ext)s',
        'verbose': True  # Gibt ausführliche Informationen aus
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# Beispielaufruf
download_video('https://www.youtube.com/watch?v=hI9HQfCAw64')


app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"

# HTML für die Benutzeroberfläche
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f9f9f9;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            text-align: center;
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            max-width: 400px;
            width: 100%;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
        }
        input {
            width: calc(100% - 20px);
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        button {
            background-color: #007bff;
            color: #fff;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
        p {
            margin-top: 10px;
            color: #555;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>YouTube Downloader</h1>
        <p>Geben Sie die URL des YouTube-Videos ein:</p>
        <input type="text" id="videoUrl" placeholder="YouTube-URL hier eingeben">
        <select id="formatSelect">
            <option value="video">Video (MP4)</option>
            <option value="audio">Audio (MP3)</option>
        </select>
        <button id="downloadBtn">Download</button>
        <p id="status"></p>
    </div>
    <script>
        document.getElementById('downloadBtn').addEventListener('click', () => {
            const videoUrl = document.getElementById('videoUrl').value;
            const format = document.getElementById('formatSelect').value;
            const status = document.getElementById('status');

            if (!videoUrl) {
                status.textContent = "Bitte geben Sie eine gültige URL ein.";
                status.style.color = "red";
                return;
            }

            status.textContent = "Download wird gestartet...";
            status.style.color = "black";

            fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: videoUrl, format }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    status.innerHTML = `Download erfolgreich! <a href="${data.file}" target="_blank">Herunterladen</a>`;
                    status.style.color = "green";
                } else {
                    status.textContent = `Fehler: ${data.message}`;
                    status.style.color = "red";
                }
            })
            .catch(error => {
                status.textContent = "Ein Fehler ist aufgetreten.";
                status.style.color = "red";
                console.error('Fehler:', error);
            });
        });
    </script>
</body>
</html>
"""

def download_video(url, output_folder, download_audio=False):
    """
    Lädt ein YouTube-Video oder nur die Audiospur herunter.
    :param url: Die URL des YouTube-Videos.
    :param output_folder: Der Ordner, in dem die Datei gespeichert wird.
    :param download_audio: Wenn True, wird nur die Audiospur heruntergeladen.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    ydl_opts = {
        'outtmpl': f'{output_folder}/%(title)s.%(ext)s',
        'format': 'bestaudio[ext=m4a]/mp3' if download_audio else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'merge_output_format': 'mp4' if not download_audio else None,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}] if download_audio else [],
        'quiet': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        raise e

@app.route('/')
def index():
    return render_template_string(HTML_CONTENT)

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.json
        url = data.get('url')
        format_type = data.get('format')

        if not url:
            return jsonify({'success': False, 'message': 'Keine URL angegeben.'})

        if format_type == "audio":
            filename = download_video(url, DOWNLOAD_FOLDER, download_audio=True)
        else:
            filename = download_video(url, DOWNLOAD_FOLDER, download_audio=False)

        return jsonify({'success': True, 'file': f'/files/{os.path.basename(filename)}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/files/<filename>')
def serve_file(filename):
    try:
        return send_file(os.path.join(DOWNLOAD_FOLDER, filename), as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
    app.run(debug=True)
