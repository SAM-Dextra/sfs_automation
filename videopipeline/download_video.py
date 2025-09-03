import argparse
import os
import re
import gdown

def parse_gdrive_id(url: str) -> str:
    """
    Extract Google Drive file ID from different types of URLs.
    """
    patterns = [
        r"id=([a-zA-Z0-9_-]+)",
        r"/d/([a-zA-Z0-9_-]+)"
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise ValueError(f"Could not extract file id from url: {url}")


def gdrive_download(url: str, output: str):
    """
    Download file from Google Drive using gdown.
    """
    file_id = parse_gdrive_id(url)
    download_url = f"https://drive.google.com/uc?id={file_id}"

    os.makedirs(os.path.dirname(output), exist_ok=True)
    gdown.download(download_url, output, quiet=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Google Drive file URL")
    parser.add_argument("--output", required=True, help="Output file path")
    args = parser.parse_args()

    print(f"📥 Downloading from Google Drive (id={parse_gdrive_id(args.url)}) → {args.output}")
    gdrive_download(args.url, args.output)
    print("✅ Download complete.")
