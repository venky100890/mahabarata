---
name: kurukshetra-asset-forge
description: Generate Kurukshetra game-art assets from a CSV manifest during the active ChatGPT session, upload every successful output to Google Drive, and maintain resumable checkpoints and QA logs.
version: 1.0.0
---

# Kurukshetra Asset Forge

## Purpose
Execute the Kurukshetra asset manifest in bounded, visible batches during the current active session. This skill never promises background execution. It generates, uploads, verifies, and checkpoints before replying.

## Required inputs
- CSV columns: `id, category, asset_name, aspect_ratio, background, prompt`
- Google Drive production-root folder URL or ID
- Batch size, default `4`, recommended maximum `8`
- Optional category/asset filter

## Global style lock
```text
STYLE: Painterly-realistic Indian epic fantasy game art for a AAA mobile strategy RPG set in the Mahabharata era. Rendering style: modern game splash-art quality — crisp digital painting, dramatic values, cinematic rim light. NOT cartoon, NOT cel-shaded, NOT anime, NOT photorealistic — high-end stylized realism (benchmark: modern gacha splash art meets Raja Ravi Varma oil-painting color sensibility).

LIGHTING: Golden-hour key light from upper left, warm saffron (#ffb833) rim light on all characters, deep crimson-night ambient shadows (#260f13). Divine/magical energy always glows teal-white (#3ee6d0) for contrast against the warm palette.

PALETTE: night crimson #0e0909→#260f13, saffron gold #ffb833, light gold #ffe08f, divine teal #3ee6d0, blood crimson #8c0d13, cream #fff6db. Gold materials must show anisotropic metallic sheen; silk must show soft sheen and drape.

QUALITY BAR: sharp focus on subject, painterly but controlled brushwork, ornate Indian jewelry and armor detail (kundala earrings, bazubands, mukut crowns, temple motifs), clean silhouette readable at small size.

AVOID: western medieval armor, generic fantasy tropes, anime faces, cel outlines, watermark, text, signature, blurry edges, extra limbs, modern objects.
```

## Active-session execution contract
For every selected pending row:
1. Replace `[PASTE GLOBAL STYLE LOCK]` with the exact style lock.
2. Append exact aspect ratio, PNG requirement, transparency when marked, maximum detail, clean edges, no text/watermark.
3. Call image generation exactly once.
4. Visually QA palette, lighting direction, silhouette, anatomy, artifacts, and transparency intent.
5. If clearly failed, regenerate once with a focused correction. Never loop indefinitely.
6. Upload accepted output immediately to the routed Drive folder.
7. Filename: `<id>__<asset_name>.png`.
8. Verify upload response includes success, file id, parent id, filename, and URL.
9. Update and upload checkpoint after every accepted asset; at minimum after each batch.
10. Stop at requested batch size or blocking tool error.

## Drive routing
- hero categories -> `01_Heroes`
- troop categories -> `02_Troops`
- building categories -> `03_Buildings`
- VFX/flipbooks/glow/particles -> `04_VFX_and_Effects`
- environments/maps/parallax -> `05_Environments_and_Maps`
- UI/icons/frames/buttons/cinematics -> `06_UI_Kit_and_Cinematics`
- unmatched -> `99_Unsorted`
Create useful subject subfolders such as `Arjuna`, `Karna`, `Fortress`, `DivineArrow`.

## Character consistency
- Generate turnaround before any later hero asset.
- Use accepted turnaround as exact image reference whenever supported.
- Prefer completing one hero within consecutive active batches.
- Use master style anchor whenever available.

## Checkpoint schema
`id,category,asset_name,status,attempts,drive_file_id,drive_url,qa_notes,updated_utc`
Statuses: `pending, generated, qa_failed, uploaded, blocked`.
Never claim completion unless every row is `uploaded`.

## Progress response
Report attempted, uploaded, regenerated, blocked, exact next pending ID, production root, checkpoint link.
Do not say work will continue by itself. The next active batch starts when user says `Run the next N assets`.

## Supported commands
- Initialize Kurukshetra asset production
- Run the next N assets
- Run the next N assets from CATEGORY
- Generate HERO_NAME completely
- Retry failed assets
- Show production status
- Package uploaded assets for Unity
- Create GitHub import manifest

## Unity packaging
Organize completed assets under `Assets/Art/Kurukshetra/<category>/<subject>/`, create JSON/CSV manifest, include transparency and slicing notes, ZIP, upload to Drive. Do not call concept-board crops final runtime sprites.
