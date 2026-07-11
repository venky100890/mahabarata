#!/usr/bin/env python3
"""Create authorized-user OAuth JSON for the Asset Forge GitHub secret.

Usage:
    pip install google-auth-oauthlib
    python tools/create_google_drive_credentials.py path/to/client_secret.json

Save the complete one-line JSON output as the GitHub Actions secret
GOOGLE_DRIVE_CREDENTIALS_JSON. Never commit the generated credentials.
"""
from __future__ import annotations

import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python tools/create_google_drive_credentials.py client_secret.json"
        )

    source = Path(sys.argv[1]).expanduser()
    if not source.is_file():
        raise SystemExit(f"OAuth client-secret file not found: {source}")

    flow = InstalledAppFlow.from_client_secrets_file(str(source), SCOPES)
    credentials = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
    )
    print(credentials.to_json())


if __name__ == "__main__":
    main()
