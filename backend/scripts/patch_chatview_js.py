"""
向 ChatView.vue 的 <script setup> 区域注入设置弹窗所需的 JS 逻辑：
- showSettings ref
- outputLength 偏好（存入 localStorage）
- 密码修改表单逻辑
"""
path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend\src\views\ChatView.vue"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 找到 const auth = useAuthStore() 所在行后注入
inject_anchor = "const auth = useAuthStore()\nconst router = useRouter()"

settings_js = """
// ====== 设置弹窗逻辑 ======
const showSettings = ref(false)
const closeSettings = () => { showSettings.value = false; pwdMsg.value = null; pwdForm.value = { oldPwd: '', newPwd: '', confirmPwd: '' } }

// 输出长度偏好
const OUTPUT_LENGTH_KEY = 'zyd_output_length'
const outputLengthOptions = [
  { value: 'short', icon: '⚡', label: '简洁', desc: '精炼核心要点，适合快速查询' },
  { value: 'medium', icon: '📋', label: '标准', desc: '均衡详细，适合日常对话' },
  { value: 'long', icon: '📄', label: '详细', desc: '完整展开，适合复杂分析' }
]
const outputLength = ref(localStorage.getItem(OUTPUT_LENGTH_KEY) || 'medium')
const setOutputLength = (val) => {
  outputLength.value = val
  localStorage.setItem(OUTPUT_LENGTH_KEY, val)
}

// 修改密码
const pwdForm = ref({ oldPwd: '', newPwd: '', confirmPwd: '' })
const pwdMsg = ref(null)
const pwdLoading = ref(false)
const submitChangePassword = async () => {
  pwdMsg.value = null
  const { oldPwd, newPwd, confirmPwd } = pwdForm.value
  if (!oldPwd || !newPwd || !confirmPwd) {
    pwdMsg.value = { type: 'error', text: '请填写所有密码字段' }
    return
  }
  if (newPwd !== confirmPwd) {
    pwdMsg.value = { type: 'error', text: '两次输入的新密码不一致' }
    return
  }
  if (newPwd.length < 6) {
    pwdMsg.value = { type: 'error', text: '新密码不能少于 6 位' }
    return
  }
  pwdLoading.value = true
  try {
    await axios.post('/api/auth/change-password', { old_password: oldPwd, new_password: newPwd })
    pwdMsg.value = { type: 'success', text: '✅ 密码修改成功！下次登录将使用新密码。' }
    pwdForm.value = { oldPwd: '', newPwd: '', confirmPwd: '' }
  } catch (err) {
    pwdMsg.value = { type: 'error', text: err?.response?.data?.detail || '修改失败，请检查当前密码是否正确' }
  } finally {
    pwdLoading.value = false
  }
}
"""

if inject_anchor in content:
    content = content.replace(inject_anchor, inject_anchor + "\n" + settings_js, 1)
    print("✅ JS 逻辑注入成功")
else:
    print("⚠️  未找到注入点，跳过")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("🎉 JS 逻辑写入完成！")
