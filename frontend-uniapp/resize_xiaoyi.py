from PIL import Image
import os

static_dir = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend-uniapp\src\static"
xiaoyi = os.path.join(static_dir, "xiaoyi_character.png")
if os.path.exists(xiaoyi):
    with Image.open(xiaoyi) as img:
        # Resize to 256x256 (enough for small icon in UI)
        img = img.resize((256, 256), Image.Resampling.LANCZOS)
        # Save it with optimization
        img.save(xiaoyi, "PNG", optimize=True)
        print(f"Resized xiaoyi_character.png to {os.path.getsize(xiaoyi)} bytes")
