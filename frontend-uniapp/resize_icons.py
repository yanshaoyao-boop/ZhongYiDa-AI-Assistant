from PIL import Image
import os

static_dir = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend-uniapp\src\static"
icons = [
    "tab_chat_active.png",
    "tab_chat_inactive.png",
    "tab_admin_active.png",
    "tab_admin_inactive.png"
]

for icon in icons:
    path = os.path.join(static_dir, icon)
    if os.path.exists(path):
        with Image.open(path) as img:
            # Resize to 81x81 (standard WeChat tabbar size)
            img = img.resize((81, 81), Image.Resampling.LANCZOS)
            # Save it with optimization
            img.save(path, "PNG", optimize=True)
            print(f"Resized {icon} to {os.path.getsize(path)} bytes")

# Also resize logo-icon.png as it was 440KB
logo_icon = os.path.join(static_dir, "logo-icon.png")
if os.path.exists(logo_icon):
    with Image.open(logo_icon) as img:
        img = img.resize((200, 200), Image.Resampling.LANCZOS)
        img.save(logo_icon, "PNG", optimize=True)
        print(f"Resized logo-icon.png to {os.path.getsize(logo_icon)} bytes")
