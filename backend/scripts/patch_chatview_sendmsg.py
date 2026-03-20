"""
在 ChatView.vue 的 sendMessage 函数中，将输出长度偏好注入到发送的消息里。
找到 history 构建的地方，在用户消息前面追加长度指令。
"""
path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend\src\views\ChatView.vue"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 找到发送 API 请求的地方，在 message 字段注入长度指令
# 通常是 axios.post('/api/chat/stream', { message: ... })
# 我们在 finalMessage 构建时加上前缀

old_send_payload = "const payload = {\n        message: userText,"
new_send_payload = """// 根据用户偏好，在消息前追加输出长度指令
        const lenHintMap = {
          short: '[输出格式偏好:极致精简,用30字以内说清楚,拒绝废话] ',
          medium: '',
          long: '[输出格式偏好:详尽展开,分点说明,可以适当列举细节] '
        }
        const lenHint = lenHintMap[outputLength.value] || ''
        const payload = {
          message: lenHint + userText,"""

if old_send_payload in content:
    content = content.replace(old_send_payload, new_send_payload, 1)
    print("✅ 输出长度偏好已注入 sendMessage")
else:
    print("⚠️  未找到 payload 构建点，跳过")
    # 打印周围内容用于 debug
    idx = content.find("const payload = {")
    print(f"找到 'const payload = {{' 位置：{idx}")
    if idx != -1:
        print(content[idx:idx+200])

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("🎉 完成！")
