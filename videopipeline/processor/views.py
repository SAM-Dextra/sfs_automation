import json
import subprocess
import download_video
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import upload_gdrive

from upload_gdrive import upload_files
from download_video import gdrive_download  # <-- Import our fixed downloader

BASE_DIR = Path(settings.BASE_DIR)

# 🔹 Replace with your Drive folder ID where videos should be uploaded
GDRIVE_FOLDER_ID = "19X28DLlPkSlJpGTGlRY7fRJvinccqvkU"

@csrf_exempt
def process_video(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)

        file_url = data["file_url"]              # Google Drive link
        splits = data["splits"]                  # e.g. [[0,10],[10,20]]
        logo = data["logo"]                      # inputs/logo.png
        intro_video = data["intro_video"]        # inputs/pre-video.mp4

        # === STEP 1: Download video ===
        input_dir = BASE_DIR / "inputs" / "videos"
        input_dir.mkdir(parents=True, exist_ok=True)
        input_file = input_dir / "input.mp4"

        gdrive_download(file_url, str(input_file))

        # === STEP 2: Process video ===
        temp_dir = BASE_DIR / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        output_dir = BASE_DIR / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        process_cmd = [
            "python3",
            str(BASE_DIR / "process_video.py"),
            "--input_dir", str(input_dir),
            "--temp_dir", str(temp_dir),
            "--output_dir", str(output_dir),
            "--splits", json.dumps(splits),
            "--logo", logo,
            "--intro_video", intro_video
        ]

        subprocess.run(process_cmd, check=True)

        # === STEP 3: Upload processed videos to Google Drive ===
        uploaded_links = upload_files(output_dir, GDRIVE_FOLDER_ID)

        # === STEP 4: Return response ===
        output_files = [f.name for f in output_dir.glob("*.mp4")]

        return JsonResponse({
            "status": "success",
            "downloaded_file": str(input_file),
            "processed_files": output_files,
            "uploaded_links": uploaded_links
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
