#!/usr/bin/env python3
"""Download the Kurukshetra CSV manifest from Google Drive.

The destination file must be shared with the configured service-account email.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


def credentials() -> service_account.Credentials:
    raw_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    encoded = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64", "").strip()
    file_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if encoded:
        raw_json = base64.b64decode(encoded).decode("utf-8")
    if raw_json:
        return service_account.Credentials.from_service_account_info(
            json.loads(raw_json), scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
    if file_path:
        return service_account.Credentials.from_service_account_file(
            file_path, scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
    raise RuntimeError("Google service-account credentials are not configured")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file-id", default=os.getenv("MANIFEST_DRIVE_FILE_ID", ""))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tools/asset_forge/data/kurukshetra_full_prompt_list.csv"),
    )
    args = parser.parse_args()
    if not args.file_id:
        raise SystemExit("Provide --file-id or MANIFEST_DRIVE_FILE_ID")

    drive = build("drive", "v3", credentials=credentials(), cache_discovery=False)
    request = drive.files().get_media(fileId=args.file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request, chunksize=5 * 1024 * 1024)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(buffer.getvalue())
    print(f"Downloaded manifest to {args.output}")


if __name__ == "__main__":
    main()
