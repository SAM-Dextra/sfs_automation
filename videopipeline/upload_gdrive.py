import os
from pathlib import Path
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


def gdrive_auth():
    gauth = GoogleAuth()

    # Configure for offline access (refresh_token)
    gauth.settings.update({
        "client_config_file": "client_secrets.json",
        "oauth_scope": [
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive"
        ],
        "get_refresh_token": True
    })

    # Try to load saved credentials
    gauth.LoadCredentialsFile("credentials.json")

    if gauth.credentials is None:
        # First time login – browser will open
        gauth.LocalWebserverAuth()
        gauth.SaveCredentialsFile("credentials.json")
    elif gauth.access_token_expired:
        # Refresh automatically
        gauth.Refresh()
        gauth.SaveCredentialsFile("credentials.json")
    else:
        # Already valid
        gauth.Authorize()

    return GoogleDrive(gauth)


def upload_files(folder, drive_folder_id):
    drive = gdrive_auth()
    folder = Path(folder)
    uploaded_urls = []

    for file_path in folder.glob("*.mp4"):
        print(f"Uploading {file_path}")
        f = drive.CreateFile({
            "title": file_path.name,
            "parents": [{"id": drive_folder_id}]
        })
        f.SetContentFile(str(file_path))
        f.Upload()

        # Make shareable
        f.InsertPermission({
            "type": "anyone",
            "value": "anyone",
            "role": "reader"
        })

        uploaded_urls.append(f"https://drive.google.com/file/d/{f['id']}/view")

    return uploaded_urls


# CLI support
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True, help="Local folder containing MP4 files")
    parser.add_argument("--drive_folder_id", required=True, help="Google Drive folder ID")
    args = parser.parse_args()

    urls = upload_files(args.input_dir, args.drive_folder_id)
    print("\n✅ Uploaded files:")
    for url in urls:
        print(url)
