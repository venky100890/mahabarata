#!/usr/bin/env python3
"""Extract the generated Kurukshetra art pack stored as Base64 chunks.

Run from the repository root:

    python tools/extract_kurukshetra_art_pack.py

This reconstructs the ZIP at:
    Assets/Art/Generated/Kurukshetra/v0_1/Package/kurukshetra_generated_art_v0_1.zip

Then extracts the source SVG, animated SVG, Lottie JSON, README, and metadata files
into Assets/Art/Generated/Kurukshetra/v0_1/.
"""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "Assets" / "Art" / "Generated" / "Kurukshetra" / "v0_1" / "Package"
OUT_ZIP = PACKAGE_DIR / "kurukshetra_generated_art_v0_1.zip"
EXPECTED_SHA256 = "d789fdb4225a1ab9938fba4ff1c871647e832f535c3880ebf4dbdf2407594f83"


def main() -> None:
    parts = sorted(PACKAGE_DIR.glob("kurukshetra_generated_art_v0_1.zip.b64.part*"))
    if not parts:
        raise SystemExit(f"No Base64 parts found in {PACKAGE_DIR}")

    encoded = "".join(p.read_text(encoding="utf-8").strip() for p in parts)
    raw = base64.b64decode(encoded)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"SHA256 mismatch: got {digest}, expected {EXPECTED_SHA256}")

    OUT_ZIP.write_bytes(raw)
    with ZipFile(OUT_ZIP) as zf:
        zf.extractall(ROOT)

    print(f"Extracted {len(parts)} parts into {OUT_ZIP}")
    print("Assets extracted under Assets/Art/Generated/Kurukshetra/v0_1/")


if __name__ == "__main__":
    main()
