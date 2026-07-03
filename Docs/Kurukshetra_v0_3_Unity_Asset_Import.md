# Kurukshetra v0.3 Unity Asset Import

This repository is prepared to receive the v0.3 PNG HQ asset pack under:

```text
Assets/Art/Kurukshetra/
```

## Current status

- `.gitattributes` has been added so PNG, GIF, MP4, ZIP, and other large art files are tracked through Git LFS.
- The v0.3 generated asset ZIP is uploaded to Google Drive: https://drive.google.com/file/d/1ahRbch26Xb_l1oAAmF8qJ-uN8vx4BLje/view?usp=drivesdk
- The Drive folder is: https://drive.google.com/drive/folders/1S49WfgaQVNfVtmlesmjQ65G1BXHJs54v
- The ZIP should be unzipped locally and committed with Git LFS so the Unity project can reference the assets directly from the repository.

## Recommended import steps

From your Unity repository root:

```bash
# 1. Install Git LFS once if needed
git lfs install

# 2. Confirm LFS patterns are active
git lfs track

# 3. Download kurukshetra_png_hq_asset_pack_v0_3.zip from Google Drive
#    https://drive.google.com/file/d/1ahRbch26Xb_l1oAAmF8qJ-uN8vx4BLje/view?usp=drivesdk

# 4. Unzip the v0.3 pack into a temporary folder
unzip ~/Downloads/kurukshetra_png_hq_asset_pack_v0_3.zip -d /tmp/kurukshetra_v0_3

# 5. Copy the Unity-ready folder into the project
mkdir -p Assets/Art
rsync -av /tmp/kurukshetra_v0_3/Assets/Art/Kurukshetra/ Assets/Art/Kurukshetra/

# 6. Open Unity once and let it generate .meta files
#    Then return to terminal and commit everything.

git status
git add .gitattributes Assets/Art/Kurukshetra Docs/Kurukshetra_v0_3_Unity_Asset_Import.md
git commit -m "Add Kurukshetra v0.3 Unity art assets"
git push
```

## Unity import settings

### Runtime UI and icons

- Texture Type: Sprite (2D and UI)
- Sprite Mode: Single
- Alpha Is Transparency: On
- Mip Maps: Off
- Compression: High Quality

### Environments

- Texture Type: Sprite or Default, depending on usage
- Max Size: 2048 or 4096
- Mip Maps: On only if used in world-space or with camera motion
- Mobile compression: ASTC 6x6 or ASTC 8x8

### Sprite sheets

- Texture Type: Sprite (2D and UI)
- Sprite Mode: Multiple
- Slice by Grid by Cell Size
- v0.3 sample sheets: 4 columns x 2 rows, 256 x 256 cells
- Use 24 FPS for generated VFX animation clips

## Suggested Addressables groups

```text
art.characters.heroes
art.characters.troops
art.ui.hud
art.ui.progression
art.vfx.combat
art.environments
art.buildings
```

## Runtime folders

```text
Assets/Art/Kurukshetra/Runtime/Characters
Assets/Art/Kurukshetra/Runtime/UI
Assets/Art/Kurukshetra/Runtime/VFX
Assets/Art/Kurukshetra/Runtime/Buildings
Assets/Art/Kurukshetra/Runtime/Environments
Assets/Art/Kurukshetra/Runtime/SpriteSheets
```

## Production note

The v0.3 pack contains high-fidelity PNG boards, runtime crops, and lightweight sample animation frames. Some assets are board-derived crops. For final launch, create clean transparent production sprites for every hero, troop, building, icon, and VFX frame.
