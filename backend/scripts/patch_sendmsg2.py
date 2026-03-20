path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend\src\views\ChatView.vue"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = "      body: JSON.stringify({\n        message: content,\n        mode: currentMode.value,"
new = "      body: JSON.stringify({\n        message: (outputLength.value === 'short' ? '[输出偏好:极致精简] ' : outputLength.value === 'long' ? '[输出偏好:详尽展开] ' : '') + content,\n        mode: currentMode.value,"

if old in content:
    content = content.replace(old, new, 1)
    print("OK - injected")
else:
    print("NOT FOUND - checking raw bytes near fetch body...")
    idx = content.find("JSON.stringify({")
    if idx >= 0:
        print(repr(content[idx:idx+120]))

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
