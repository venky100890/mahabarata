# Kurukshetra Asset Forge

This pipeline generates the 315 assets in the Kurukshetra CSV manifest in resumable batches of up to 30. Every accepted PNG is uploaded into the existing Google Drive production root, and a checkpoint is committed back to GitHub after each run.

## What it does

1. Expands the self-contained Asset Forge runtime stored in `asset_pipeline/forge_runtime.zip.b64.part*`.
2. Reads the 315-row prompt manifest.
3. Selects the next 30 eligible rows.
4. Uses `gpt-image-2` for opaque artwork and `gpt-image-1.5` for transparent PNGs.
5. Runs PNG, dimension, alpha, and vision QA.
6. Retries failed QA up to three times with correction feedback.
7. Uploads accepted images to the matching Drive category and subject folder.
8. Updates `asset_pipeline/state/checkpoint.csv` after every asset.
9. Mirrors the checkpoint and latest report into Google Drive.
10. Commits checkpoint changes into GitHub.
11. Dispatches the next batch automatically until no eligible rows remain.

## Google Drive destination

Production root folder:

```text
Kurukshetra Complete Asset Production v1.0
```

Folder ID:

```text
1cV-fAlJQjpJ-CnAZ_x27sBkR-yCpOATw
```

## Required GitHub Actions secrets

Open the repository and go to **Settings → Secrets and variables → Actions**.

Create these three repository secrets:

### `OPENAI_API_KEY`

An OpenAI API key with access to GPT Image models. OpenAI may require API organization verification for GPT Image access.

### `GOOGLE_DRIVE_ROOT_FOLDER_ID`

```text
1cV-fAlJQjpJ-CnAZ_x27sBkR-yCpOATw
```

### `GOOGLE_DRIVE_CREDENTIALS_JSON`

Authorized-user OAuth JSON with an offline refresh token for the Google account that owns the production folder.

Generate it locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install google-auth-oauthlib
python tools/create_google_drive_credentials.py ~/Downloads/client_secret.json
```

Copy the complete one-line JSON printed by the script into the GitHub secret. Never commit it.

## Start

1. Open the repository’s **Actions** tab.
2. Select **Kurukshetra Asset Forge**.
3. Click **Run workflow**.
4. Keep `batch_size=30`, `category=all`, and `auto_continue=true`.

The workflow will dispatch the next run while eligible assets remain. A 315-row clean run is approximately 11 batches; retries can add image-generation calls.

## Pause and resume

Cancel the current workflow to pause. Run it again to resume. The checkpoint and Drive-file reconciliation prevent intentional duplication.

## Cost controls

The workflow defaults to high-quality image generation and semantic QA. Review current OpenAI image pricing before launching the full manifest. To lower cost, edit `.github/workflows/kurukshetra-assets.yml` and change `IMAGE_QUALITY` to `medium`, or set `SEMANTIC_QA_ENABLED` to `false`.

## Output layout

```text
Kurukshetra Complete Asset Production v1.0/
  01_Heroes/<Subject>/<category>/
  02_Troops/<Subject>/<category>/
  03_Buildings/<Subject>/<category>/
  04_VFX_and_Effects/<Subject>/<category>/
  05_Environments_and_Maps/<Subject>/<category>/
  06_UI_Kit_and_Cinematics/<Subject>/<category>/
```

Generated names preserve manifest IDs, for example:

```text
hero_sheets_001__arjuna_turnaround.png
```

## Failure behavior

After three failed attempts, a row becomes `blocked` and automatic chaining skips it. Blocked rows can be retried later by resetting their status and attempt count in the checkpoint.
