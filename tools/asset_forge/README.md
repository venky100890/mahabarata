# Kurukshetra Asset Forge

A resumable image-production pipeline for the Kurukshetra Unity project.

It reads the Google Drive CSV manifest, generates **up to 30 assets per run**, validates the PNGs, uploads every accepted file into Google Drive, commits a checkpoint, and starts the next run until the manifest is complete.

## What is already wired

- Manifest Drive file ID: `1hG9ZtnEGhkzDcv70p6s_ayOk74fnC0UN`
- Production root: `1cV-fAlJQjpJ-CnAZ_x27sBkR-yCpOATw`
- Heroes: `1cY_wQjz8HNwx0zGG4gWSsZcLLr1sHKR9`
- Troops: `1My-mJfQ30XZq7gFmn-QlBZaQ9bO6Q8wU`
- Buildings: `1VMCyofxXN-WAFO_OA9PZoqp6hdvs2AAm`
- VFX: `1i8_8UxEs2w4EVv7FVu2uWPlO36hvJxWM`
- Environments: `1uaxY2Li0j-LEV80tZkWLIacXUwh8yRaT`
- UI and cinematics: `1ispVVJwPcDwzOfJrsAYSh45TA3VumTai`

Add these as GitHub **Actions variables** using the names below.

## Required GitHub secrets

In the repository, open **Settings → Secrets and variables → Actions**.

### `OPENAI_API_KEY`

An OpenAI API key with access to GPT Image models.

### `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`

1. Create a Google Cloud service account.
2. Enable the Google Drive API.
3. Download the service-account JSON key.
4. Base64-encode the entire JSON file:

```bash
base64 < service-account.json | tr -d '\n'
```

5. Add the output as this GitHub secret.
6. Share the production root folder and the manifest CSV with the service-account email as **Editor**.

### `ASSET_FORGE_PAT`

A fine-grained GitHub personal access token for this repository with:

- Actions: read/write
- Contents: read/write

This lets one completed batch dispatch the next batch immediately. Without it, the scheduled workflow resumes every six hours.

## Required GitHub variables

Create repository Actions variables:

```text
MANIFEST_DRIVE_FILE_ID=1hG9ZtnEGhkzDcv70p6s_ayOk74fnC0UN
DRIVE_ROOT_FOLDER_ID=1cV-fAlJQjpJ-CnAZ_x27sBkR-yCpOATw
DRIVE_HEROES_FOLDER_ID=1cY_wQjz8HNwx0zGG4gWSsZcLLr1sHKR9
DRIVE_TROOPS_FOLDER_ID=1My-mJfQ30XZq7gFmn-QlBZaQ9bO6Q8wU
DRIVE_BUILDINGS_FOLDER_ID=1VMCyofxXN-WAFO_OA9PZoqp6hdvs2AAm
DRIVE_VFX_FOLDER_ID=1i8_8UxEs2w4EVv7FVu2uWPlO36hvJxWM
DRIVE_ENVIRONMENTS_FOLDER_ID=1uaxY2Li0j-LEV80tZkWLIacXUwh8yRaT
DRIVE_UI_FOLDER_ID=1ispVVJwPcDwzOfJrsAYSh45TA3VumTai
```

Optional variables:

```text
OPENAI_IMAGE_MODEL=gpt-image-2
OPENAI_TRANSPARENT_IMAGE_MODEL=gpt-image-1.5
OPENAI_IMAGE_QUALITY=high
```

`gpt-image-2` is used for opaque assets. A transparent-capable model is used when the CSV marks an asset as transparent.

## Start the complete run

1. Open the repository's **Actions** tab.
2. Select **Kurukshetra Asset Forge**.
3. Select **Run workflow**.
4. Keep:
   - Batch size: `30`
   - Continue until done: enabled
5. Run it on `main`.

Each run:

1. Downloads the latest CSV from Drive.
2. Skips rows already marked `uploaded`.
3. Generates up to 30 pending images.
4. Validates PNG integrity, minimum resolution, and alpha for transparent assets.
5. Uploads each accepted image using a resumable Drive upload.
6. Commits `tools/asset_forge/state/checkpoint.csv`.
7. Dispatches the next batch while work remains.

## Local usage

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r tools/asset_forge/requirements.txt

python tools/asset_forge/sync_manifest.py \
  --file-id 1hG9ZtnEGhkzDcv70p6s_ayOk74fnC0UN

python tools/asset_forge/generate_assets.py --batch-size 30
```

Run all batches in one local process:

```bash
python tools/asset_forge/generate_assets.py --all --batch-size 30
```

Resume is automatic because the checkpoint is written after every individual asset.

## Selective runs

```bash
python tools/asset_forge/generate_assets.py --category hero_sheets --batch-size 30
python tools/asset_forge/generate_assets.py --name-filter arjuna --batch-size 30
python tools/asset_forge/generate_assets.py --status
```

## Cost and correctness controls

- Maximum batch size is intentionally capped at 30.
- An asset is retried up to three times before being marked `blocked`.
- Generated images are uploaded to Drive; they are not committed to GitHub.
- The repository stores only code and the checkpoint.
- Review the first hero turnaround before allowing the full expensive run if character canon has not yet been approved.
