# Kurukshetra Generated Art Asset Pack v0.1

This folder contains the first generated visual asset batch for **Kurukshetra: Rise of the Legends**.

## Included assets

| Asset | Type | Suggested use |
|---|---:|---|
| `Concepts/hero_arjuna_high_fidelity.svg` | High-fidelity vector hero concept | Arjuna hero card, portrait placeholder, store art mockup |
| `Concepts/battlefield_sunset_panorama.svg` | High-fidelity vector environment | Loading screen, campaign backdrop, marketing blockout |
| `Concepts/hastinapura_fortress_base.svg` | High-fidelity vector base concept | Base-building screen, tutorial backdrop, building UI mockup |
| `Animations/divine_arrow_charge_loop.svg` | Animated SVG loop | Hero ability charge VFX |
| `Animations/war_banner_idle_loop.svg` | Animated SVG loop | Alliance/banner idle animation |
| `Animations/shield_powerup_loop.svg` | Animated SVG loop | Buff/power-up VFX |
| `Animations/divine_arrow_charge_sprite_sheet_8frames.svg` | Vector sprite-sheet source | Rasterize to 8 x 512px frames for Unity |
| `Lottie/divine_arrow_charge_loop.json` | Lottie-style UI animation | Ability button charge/reward reveal |

## Unity import notes

1. Keep the SVG files as editable source masters.
2. For production mobile builds, rasterize static concepts to PNG/WebP at the target sizes needed by the UI.
3. For animated SVG loops, either use a compatible SVG renderer or export frames into sprite sheets.
4. The included Lottie JSON can be tested with a Unity Lottie-compatible runtime for UI-only motion.
5. Track runtime-ready exports separately from source masters, for example:
   - `Assets/Art/Runtime/UI/HeroCards/`
   - `Assets/Art/Runtime/VFX/SpriteSheets/`

## Art direction

Cinematic Indian-epic fantasy with readable mobile silhouettes, saffron/gold divine energy, deep indigo shadows, ornate geometric borders, dust-heavy battlefield environments, and faction-colored banners.

## Production status

These are generated source assets suitable for prototype, art direction, pitch, UI mockups, and early implementation. Before final commercial launch, review them with an artist/art director and replace or polish any assets that need hand-authored quality control.
