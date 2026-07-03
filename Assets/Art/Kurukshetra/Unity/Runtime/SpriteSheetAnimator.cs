using UnityEngine;
using UnityEngine.UI;

public class SpriteSheetAnimator : MonoBehaviour
{
    public Image targetImage;
    public Sprite[] frames;
    public float framesPerSecond = 24f;
    public bool loop = true;

    private int index;
    private float timer;

    void Reset()
    {
        targetImage = GetComponent<Image>();
    }

    void Update()
    {
        if (targetImage == null || frames == null || frames.Length == 0) return;

        timer += Time.deltaTime;
        float frameTime = 1f / Mathf.Max(1f, framesPerSecond);

        while (timer >= frameTime)
        {
            timer -= frameTime;
            index++;
            if (index >= frames.Length)
            {
                index = loop ? 0 : frames.Length - 1;
            }
            targetImage.sprite = frames[index];
        }
    }
}
