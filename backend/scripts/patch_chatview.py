"""
对 ChatView.vue 三处修改：
1. 在 sidebar-footer 中，admin 按钮上方插入 设置 按钮
2. 在 Teleport 区域末尾插入 设置弹窗 HTML
3. 在 import 中补充 Settings 图标
"""
import re

path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend\src\views\ChatView.vue"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# ===== 修改 1：在 sidebar-footer 中的 admin 按钮上方加"设置"按钮 =====
old_footer = '''      <div class="sidebar-footer">
        <a v-if="auth.isAdmin" href="/admin" target="_blank" class="sidebar-admin-btn">'''
new_footer = '''      <div class="sidebar-footer">
        <!-- 设置按钮 -->
        <button class="sidebar-settings-btn" @click="showSettings = true">
          <IconSettings size="16" /> 设置
        </button>
        <a v-if="auth.isAdmin" href="/admin" target="_blank" class="sidebar-admin-btn">'''

if old_footer in content:
    content = content.replace(old_footer, new_footer, 1)
    print("✅ 修改1：设置按钮已插入")
else:
    print("⚠️  修改1：未找到目标片段，跳过")

# ===== 修改 2：在最后一个 </Teleport> 前插入设置弹窗 =====
settings_modal_html = '''
    <!-- 设置弹窗 -->
    <Teleport to="body">
      <div v-if="showSettings" class="premium-modal-backdrop" @click.self="closeSettings">
        <div class="premium-modal settings-modal animate-modal">
          <div class="modal-header">
            <div class="header-top">
              <div class="header-main">
                <IconSettings class="header-icon" />
                <h3>用户设置</h3>
              </div>
              <button class="close-btn-inner" @click="closeSettings"><IconX /></button>
            </div>
          </div>

          <div class="modal-body custom-scrollbar">
            <!-- 输出长度 -->
            <div class="settings-section">
              <div class="settings-label">📝 小易回复长度偏好</div>
              <p class="settings-desc">控制小易每次回答内容的详尽程度</p>
              <div class="output-length-group">
                <button
                  v-for="opt in outputLengthOptions"
                  :key="opt.value"
                  :class="['length-btn', { active: outputLength === opt.value }]"
                  @click="setOutputLength(opt.value)"
                >
                  <span class="length-icon">{{ opt.icon }}</span>
                  <span class="length-label">{{ opt.label }}</span>
                  <span class="length-desc">{{ opt.desc }}</span>
                </button>
              </div>
            </div>

            <div class="settings-divider"></div>

            <!-- 修改密码 -->
            <div class="settings-section">
              <div class="settings-label">🔑 修改密码</div>
              <p class="settings-desc">修改您的登录密码（至少 6 位）</p>
              <div class="pwd-form">
                <input
                  v-model="pwdForm.oldPwd"
                  type="password"
                  placeholder="请输入当前密码"
                  class="settings-input"
                />
                <input
                  v-model="pwdForm.newPwd"
                  type="password"
                  placeholder="请输入新密码（至少 6 位）"
                  class="settings-input"
                />
                <input
                  v-model="pwdForm.confirmPwd"
                  type="password"
                  placeholder="再次确认新密码"
                  class="settings-input"
                />
                <div v-if="pwdMsg" :class="['pwd-msg', pwdMsg.type]">{{ pwdMsg.text }}</div>
                <button class="pwd-submit-btn" @click="submitChangePassword" :disabled="pwdLoading">
                  {{ pwdLoading ? '提交中...' : '确认修改' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>'''

# 在最后一个 </Teleport> 的前面（即 </div>\n</template> 之前的那个 </Teleport>）后插入
# 找到最后一个 </Teleport>
last_teleport_idx = content.rfind('    </Teleport>')
if last_teleport_idx != -1:
    insert_pos = last_teleport_idx + len('    </Teleport>')
    content = content[:insert_pos] + '\n' + settings_modal_html + content[insert_pos:]
    print("✅ 修改2：设置弹窗 HTML 已插入")
else:
    print("⚠️  修改2：未找到 </Teleport> 结束标签")

# ===== 修改 3：在 import 中补充 Settings 图标 =====
old_import_end = "  Trophy as IconTrophy\n} from 'lucide-vue-next'"
new_import_end = "  Trophy as IconTrophy,\n  Settings as IconSettings\n} from 'lucide-vue-next'"
if old_import_end in content:
    content = content.replace(old_import_end, new_import_end, 1)
    print("✅ 修改3：Settings 图标 import 已补充")
else:
    print("⚠️  修改3：未找到 import 结束行，跳过")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("\n🎉 ChatView.vue 修改完成！")
