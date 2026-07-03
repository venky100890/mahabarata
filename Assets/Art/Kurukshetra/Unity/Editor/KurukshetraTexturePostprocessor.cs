using UnityEditor;
using UnityEngine;

public class KurukshetraTexturePostprocessor : AssetPostprocessor
{
    void OnPreprocessTexture()
    {
        if (!assetPath.Contains("Assets/Art/Kurukshetra/Runtime/")) return;

        TextureImporter importer = (TextureImporter)assetImporter;
        importer.textureType = TextureImporterType.Sprite;
        importer.alphaIsTransparency = true;
        importer.mipmapEnabled = assetPath.Contains("/Environments/");
        importer.filterMode = FilterMode.Bilinear;
        importer.textureCompression = TextureImporterCompression.CompressedHQ;

        importer.spriteImportMode = assetPath.Contains("/SpriteSheets/")
            ? SpriteImportMode.Multiple
            : SpriteImportMode.Single;

        TextureImporterPlatformSettings android = new TextureImporterPlatformSettings
        {
            name = "Android",
            overridden = true,
            maxTextureSize = assetPath.Contains("/Environments/") ? 4096 : 2048,
            format = TextureImporterFormat.ASTC_6x6,
            compressionQuality = 80
        };
        importer.SetPlatformTextureSettings(android);

        TextureImporterPlatformSettings ios = new TextureImporterPlatformSettings
        {
            name = "iPhone",
            overridden = true,
            maxTextureSize = assetPath.Contains("/Environments/") ? 4096 : 2048,
            format = TextureImporterFormat.ASTC_6x6,
            compressionQuality = 80
        };
        importer.SetPlatformTextureSettings(ios);
    }
}
