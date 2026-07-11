#!/usr/bin/env python3
"""Kurukshetra Asset Forge.

Reads the CSV manifest, generates assets in resumable batches, uploads each image
into Google Drive, and writes a checkpoint after every asset.

Examples:
    python tools/asset_forge/generate_assets.py --batch-size 30
    python tools/asset_forge/generate_assets.py --all --batch-size 30
    python tools/asset_forge/generate_assets.py --category hero_sheets --batch-size 30
"""
from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import logging
import os
import random
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from openai import BadRequestError, OpenAI, RateLimitError
from PIL import Image

LOG = logging.getLogger("kurukshetra_asset_forge")

STYLE_LOCK = """STYLE: Painterly-realistic Indian epic fantasy game art for a AAA mobile strategy RPG set in the Mahabharata era. Rendering style: modern game splash-art quality — crisp digital painting, dramatic values, cinematic rim light. NOT cartoon, NOT cel-shaded, NOT anime, NOT photorealistic — high-end stylized realism (benchmark: modern gacha splash art meets Raja Ravi Varma oil-painting color sensibility).

LIGHTING: Golden-hour key light from upper left, warm saffron (#ffb833) rim light on all characters, deep crimson-night ambient shadows (#260f13). Divine/magical energy always glows teal-white (#3ee6d0) for contrast against the warm palette.

PALETTE: night crimson #0e0909→#260f13, saffron gold #ffb833, light gold #ffe08f, divine teal #3ee6d0, blood crimson #8c0d13, cream #fff6db. Gold materials must show anisotropic metallic sheen; silk must show soft sheen and drape.

QUALITY BAR: sharp focus on subject, painterly but controlled brushwork, ornate Indian jewelry and armor detail (kundala earrings, bazubands, mukut crowns, temple motifs), clean silhouette readable at small size.

AVOID: western medieval armor, generic fantasy tropes, anime faces, cel outlines, watermark, text, signature, blurry edges, extra limbs, modern objects."""

CATEGORY_PARENT_ENV = {
    "hero": "DRIVE_HEROES_FOLDER_ID",
    "troop": "DRIVE_TROOPS_FOLDER_ID",
    "building": "DRIVE_BUILDINGS_FOLDER_ID",
    "vfx": "DRIVE_VFX_FOLDER_ID",
    "environment": "DRIVE_ENVIRONMENTS_FOLDER_ID",
    "ui": "DRIVE_UI_FOLDER_ID",
}


@dataclass
class AssetRow:
    id: str
    category: str
    asset_name: str
    aspect_ratio: str
    background: str
    prompt: str


@dataclass
class Checkpoint:
    id: str
    status: str = "pending"
    attempts: int = 0
    file_path: str = ""
    drive_file_id: str = ""
    drive_url: str = ""
    error: str = ""
    updated_utc: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slug(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9._-]+", "_", value.strip())
    return clean.strip("_") or "asset"


def read_manifest(path: Path) -> list[AssetRow]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"id", "category", "asset_name", "aspect_ratio", "background", "prompt"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Manifest missing columns: {sorted(missing)}")
        rows = [AssetRow(**{key: (row.get(key) or "").strip() for key in required}) for row in reader]
    ids = [row.id for row in rows]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        raise ValueError(f"Duplicate manifest IDs: {duplicates[:20]}")
    return rows


def load_checkpoint(path: Path, rows: Iterable[AssetRow]) -> dict[str, Checkpoint]:
    state: dict[str, Checkpoint] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                row["attempts"] = int(row.get("attempts") or 0)
                state[row["id"]] = Checkpoint(**row)
    for asset in rows:
        state.setdefault(asset.id, Checkpoint(id=asset.id))
    return state


def save_checkpoint(path: Path, rows: list[AssetRow], state: dict[str, Checkpoint]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    fields = list(Checkpoint.__dataclass_fields__)
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(state[row.id]))
    tmp.replace(path)


def parse_service_account() -> service_account.Credentials:
    raw_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    encoded = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64", "").strip()
    file_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if encoded:
        raw_json = base64.b64decode(encoded).decode("utf-8")
    if raw_json:
        info = json.loads(raw_json)
        return service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/drive.file"]
        )
    if file_path:
        return service_account.Credentials.from_service_account_file(
            file_path, scopes=["https://www.googleapis.com/auth/drive.file"]
        )
    raise RuntimeError(
        "Set GOOGLE_SERVICE_ACCOUNT_JSON_BASE64, GOOGLE_SERVICE_ACCOUNT_JSON, "
        "or GOOGLE_APPLICATION_CREDENTIALS. Share destination Drive folders with "
        "the service-account email as Editor."
    )


def category_group(category: str, asset_name: str) -> str:
    value = f"{category} {asset_name}".lower()
    if any(token in value for token in ("hero", "card", "rigging", "chibi")):
        return "hero"
    if any(token in value for token in ("troop", "unit", "archer", "spearman", "cavalry", "elephant")):
        return "troop"
    if any(token in value for token in ("building", "fortress", "barracks", "temple", "stable", "tower", "wall")):
        return "building"
    if any(token in value for token in ("vfx", "effect", "flipbook", "particle", "glow", "impact", "projectile")):
        return "vfx"
    if any(token in value for token in ("environment", "map", "parallax", "arena", "biome", "sky", "ground")):
        return "environment"
    return "ui"


def drive_parent_id(asset: AssetRow) -> str:
    group = category_group(asset.category, asset.asset_name)
    env_name = CATEGORY_PARENT_ENV[group]
    value = os.getenv(env_name, "").strip()
    if value:
        return value
    fallback = os.getenv("DRIVE_ROOT_FOLDER_ID", "").strip()
    if not fallback:
        raise RuntimeError(f"Set {env_name} or DRIVE_ROOT_FOLDER_ID")
    return fallback


def aspect_to_size(aspect: str, model: str) -> str:
    normalized = aspect.replace(" ", "")
    if model == "gpt-image-2":
        return {
            "1:1": "2048x2048",
            "2:3": "2160x3240",
            "3:2": "3240x2160",
            "4:3": "3072x2304",
            "16:9": "3840x2160",
            "21:9": "3360x1440",
            "2:1": "3072x1536",
        }.get(normalized, "2048x2048")
    # Earlier GPT Image models use the legacy supported sizes.
    return {
        "1:1": "1024x1024",
        "2:3": "1024x1536",
        "3:2": "1536x1024",
        "4:3": "1536x1024",
        "16:9": "1536x1024",
        "21:9": "1536x1024",
        "2:1": "1536x1024",
    }.get(normalized, "1024x1024")


def requires_transparency(asset: AssetRow) -> bool:
    return "transparent" in asset.background.lower() or "transparent" in asset.prompt.lower()


def expand_prompt(asset: AssetRow) -> str:
    prompt = asset.prompt.replace("[PASTE GLOBAL STYLE LOCK]", STYLE_LOCK)
    constraints = [
        f"OUTPUT REQUIREMENTS: exact composition for {asset.aspect_ratio} aspect ratio.",
        "Output a single polished production asset, PNG, maximum detail, clean edges, no compression artifacts.",
        "Do not include labels, captions, legends, frames, filenames, watermarks, or signatures unless explicitly requested.",
    ]
    if requires_transparency(asset):
        constraints.append(
            "TRUE TRANSPARENT BACKGROUND REQUIRED: preserve alpha around the isolated subject; no checkerboard, no matte, no scenery."
        )
    return f"{prompt}\n\n" + "\n".join(constraints)


def call_with_retry(func, attempts: int = 4):
    for index in range(attempts):
        try:
            return func()
        except (RateLimitError, TimeoutError, ConnectionError) as exc:
            if index == attempts - 1:
                raise
            delay = min(60, (2 ** index) * 4 + random.random() * 3)
            LOG.warning("Transient API error: %s; retrying in %.1fs", exc, delay)
            time.sleep(delay)


def generate_image(client: OpenAI, asset: AssetRow) -> bytes:
    transparent = requires_transparency(asset)
    opaque_model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")
    transparent_model = os.getenv("OPENAI_TRANSPARENT_IMAGE_MODEL", "gpt-image-1.5")
    model = transparent_model if transparent else opaque_model
    kwargs = {
        "model": model,
        "prompt": expand_prompt(asset),
        "size": aspect_to_size(asset.aspect_ratio, model),
        "quality": os.getenv("OPENAI_IMAGE_QUALITY", "high"),
        "output_format": "png",
        "moderation": os.getenv("OPENAI_IMAGE_MODERATION", "auto"),
    }
    if transparent:
        kwargs["background"] = "transparent"
    result = call_with_retry(lambda: client.images.generate(**kwargs))
    if not result.data or not result.data[0].b64_json:
        raise RuntimeError("Image API returned no b64_json payload")
    return base64.b64decode(result.data[0].b64_json)


def validate_png(image_bytes: bytes, transparent_expected: bool) -> tuple[bool, str]:
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.verify()
        with Image.open(io.BytesIO(image_bytes)) as image:
            width, height = image.size
            if min(width, height) < 768:
                return False, f"resolution too small: {width}x{height}"
            if transparent_expected:
                if image.mode not in ("RGBA", "LA"):
                    return False, f"transparent asset lacks alpha channel: {image.mode}"
                alpha = image.getchannel("A")
                extrema = alpha.getextrema()
                if extrema[0] == 255:
                    return False, "transparent asset alpha channel is fully opaque"
            return True, f"valid PNG {width}x{height}, mode={image.mode}"
    except Exception as exc:  # noqa: BLE001
        return False, f"invalid PNG: {exc}"


def upload_to_drive(drive, file_path: Path, asset: AssetRow) -> dict:
    metadata = {
        "name": file_path.name,
        "parents": [drive_parent_id(asset)],
        "description": json.dumps(
            {
                "manifest_id": asset.id,
                "category": asset.category,
                "asset_name": asset.asset_name,
                "aspect_ratio": asset.aspect_ratio,
                "generated_utc": utc_now(),
            }
        ),
    }
    media = MediaFileUpload(str(file_path), mimetype="image/png", resumable=True, chunksize=5 * 1024 * 1024)
    request = drive.files().create(body=metadata, media_body=media, fields="id,name,webViewLink,parents")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            LOG.info("Uploading %s: %d%%", file_path.name, int(status.progress() * 100))
    return response


def select_pending(
    rows: list[AssetRow], state: dict[str, Checkpoint], category: str | None, name_filter: str | None
) -> list[AssetRow]:
    result = []
    for row in rows:
        checkpoint = state[row.id]
        if checkpoint.status == "uploaded":
            continue
        if category and row.category != category:
            continue
        if name_filter and name_filter.lower() not in row.asset_name.lower():
            continue
        result.append(row)
    return result


def run_batch(
    rows: list[AssetRow],
    state: dict[str, Checkpoint],
    checkpoint_path: Path,
    output_dir: Path,
    limit: int,
    category: str | None,
    name_filter: str | None,
    max_asset_attempts: int,
) -> tuple[int, int]:
    client = OpenAI()
    credentials = parse_service_account()
    drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
    pending = select_pending(rows, state, category, name_filter)[:limit]
    if not pending:
        return 0, 0

    uploaded = 0
    for index, asset in enumerate(pending, start=1):
        checkpoint = state[asset.id]
        checkpoint.attempts += 1
        checkpoint.status = "generating"
        checkpoint.updated_utc = utc_now()
        save_checkpoint(checkpoint_path, rows, state)
        LOG.info("[%d/%d] Generating %s", index, len(pending), asset.id)
        try:
            image_bytes = generate_image(client, asset)
            valid, qa = validate_png(image_bytes, requires_transparency(asset))
            if not valid:
                if checkpoint.attempts < max_asset_attempts:
                    checkpoint.status = "pending"
                    checkpoint.error = qa
                else:
                    checkpoint.status = "blocked"
                    checkpoint.error = qa
                checkpoint.updated_utc = utc_now()
                save_checkpoint(checkpoint_path, rows, state)
                LOG.error("QA failed for %s: %s", asset.id, qa)
                continue

            category_dir = output_dir / slug(asset.category)
            category_dir.mkdir(parents=True, exist_ok=True)
            file_path = category_dir / f"{slug(asset.id)}__{slug(asset.asset_name)}.png"
            file_path.write_bytes(image_bytes)
            checkpoint.file_path = str(file_path)
            checkpoint.status = "generated"
            checkpoint.error = ""
            checkpoint.updated_utc = utc_now()
            save_checkpoint(checkpoint_path, rows, state)

            result = upload_to_drive(drive, file_path, asset)
            checkpoint.status = "uploaded"
            checkpoint.drive_file_id = result["id"]
            checkpoint.drive_url = result.get("webViewLink", "")
            checkpoint.error = qa
            checkpoint.updated_utc = utc_now()
            uploaded += 1
            LOG.info("Uploaded %s: %s", asset.id, checkpoint.drive_url)
        except BadRequestError as exc:
            checkpoint.status = "blocked" if checkpoint.attempts >= max_asset_attempts else "pending"
            checkpoint.error = f"OpenAI bad request: {exc}"
            checkpoint.updated_utc = utc_now()
            LOG.exception("Generation blocked for %s", asset.id)
        except Exception as exc:  # noqa: BLE001
            checkpoint.status = "blocked" if checkpoint.attempts >= max_asset_attempts else "pending"
            checkpoint.error = str(exc)[:1000]
            checkpoint.updated_utc = utc_now()
            LOG.exception("Failed asset %s", asset.id)
        finally:
            save_checkpoint(checkpoint_path, rows, state)
    return len(pending), uploaded


def summarize(rows: list[AssetRow], state: dict[str, Checkpoint]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for row in rows:
        status = state[row.id].status
        totals[status] = totals.get(status, 0) + 1
    return dict(sorted(totals.items()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("tools/asset_forge/data/kurukshetra_full_prompt_list.csv"))
    parser.add_argument("--checkpoint", type=Path, default=Path("tools/asset_forge/state/checkpoint.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("generated_assets"))
    parser.add_argument("--batch-size", type=int, default=30)
    parser.add_argument("--all", action="store_true", help="Run repeated batches until no pending assets remain")
    parser.add_argument("--max-batches", type=int, default=0, help="Safety cap for --all; 0 means unlimited")
    parser.add_argument("--category")
    parser.add_argument("--name-filter")
    parser.add_argument("--max-asset-attempts", type=int, default=3)
    parser.add_argument("--status", action="store_true")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    if args.batch_size < 1 or args.batch_size > 30:
        raise ValueError("--batch-size must be between 1 and 30")
    rows = read_manifest(args.manifest)
    state = load_checkpoint(args.checkpoint, rows)
    save_checkpoint(args.checkpoint, rows, state)
    if args.status:
        print(json.dumps(summarize(rows, state), indent=2))
        return 0

    batch_number = 0
    while True:
        attempted, uploaded = run_batch(
            rows=rows,
            state=state,
            checkpoint_path=args.checkpoint,
            output_dir=args.output_dir,
            limit=args.batch_size,
            category=args.category,
            name_filter=args.name_filter,
            max_asset_attempts=args.max_asset_attempts,
        )
        batch_number += 1
        LOG.info("Batch %d complete: attempted=%d uploaded=%d status=%s", batch_number, attempted, uploaded, summarize(rows, state))
        if not args.all or attempted == 0:
            break
        if args.max_batches and batch_number >= args.max_batches:
            LOG.warning("Reached --max-batches=%d", args.max_batches)
            break
    print(json.dumps(summarize(rows, state), indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        LOG.warning("Interrupted; checkpoint is safe for resume")
        sys.exit(130)
