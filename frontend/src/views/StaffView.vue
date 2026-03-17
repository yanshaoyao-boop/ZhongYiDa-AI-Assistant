<template>
  <div class="staff-container">
    <header class="staff-header glass-panel">
      <div class="header-main">
        <div class="header-left">
          <router-link to="/admin" class="back-link">← 返回后台</router-link>
          <h1>小易助号管理</h1>
        </div>
        <div class="header-right">
          <button @click="handleExport" class="btn-outline">
             导出 Excel
          </button>
          <button @click="triggerImport" class="btn-outline">
             导入 Excel
          </button>
          <input type="file" ref="importInput" style="display:none" @change="handleImport" accept=".xlsx,.xls" />
          <button @click="openTemplateModal" class="btn-outline">
             权限模板
          </button>
          <button v-if="auth.canManageAllBranches" @click="openOrgModal" class="btn-outline">
             架构管理
          </button>
          <button @click="openUserModal(null)" class="btn-primary">
            + {{ auth.canManageAllBranches ? '新增员工' : '新增本分公司员工' }}
          </button>
        </div>
      </div>
    </header>

    <div class="staff-content">
      <!-- Summary Cards -->
      <div class="summary-grid">
        <div class="summary-card glass-panel">
          <div class="card-icon blue"><IconUsers /></div>
          <div class="card-info">
            <span class="label">全系统活跃员工</span>
            <span class="value">{{ users.filter(u => u.is_active).length }}</span>
          </div>
        </div>
        <div class="summary-card glass-panel">
          <div class="card-icon purple"><IconBuilding /></div>
          <div class="card-info">
            <span class="label">覆盖分公司</span>
            <span class="value">{{ structure.length }}</span>
          </div>
        </div>
      </div>

      <!-- Users Table -->
      <div class="table-container glass-panel">
        <div class="table-header">
          <h2>员工列表</h2>
          <div class="table-filters">
            <input v-model="searchQuery" type="text" placeholder="搜索用户名..." class="search-input" />
          </div>
        </div>
        
        <div class="table-scroll">
          <table class="staff-table">
            <thead>
              <tr>
                <th>登录名</th>
                <th>用户名</th>
                <th>所属分公司</th>
                <th>所属部门</th>
                <th>角色</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in filteredUsers" :key="user.id">
                <td>{{ user.username }}</td>
                <td>{{ user.full_name || '-' }}</td>
                <td>{{ user.branch || '未分配' }}</td>
                <td>{{ user.department || '未分配' }}</td>
                <td>
                  <span :class="['role-tag', user.role]">
                    {{ roleMap[user.role] }}
                  </span>
                </td>
                <td>
                  <span :class="['status-dot', { active: user.is_active }]"></span>
                  {{ user.is_active ? '启用' : '禁用' }}
                </td>
                <td class="actions">
                  <button @click="openUserModal(user)" class="icon-btn edit" title="编辑"><IconEdit size="18" /></button>
                  <button @click="openPasswordModal(user)" class="icon-btn password" title="修改密码"><IconKeyRound size="18" /></button>
                  <button @click="handleDeleteUser(user)" class="icon-btn delete" title="删除"><IconTrash size="18" /></button>
                </td>
              </tr>
              <tr v-if="filteredUsers.length === 0">
                <td colspan="7" class="empty-cell">未找到相关人员数据</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- User Edit/Create Modal -->
    <div v-if="showUserModal" class="modal-overlay" @click.self="showUserModal = false">
      <div class="modal-card glass-panel">
        <div class="modal-header">
          <h3>{{ editingUser ? '编辑员工' : '新增员工' }}</h3>
          <button @click="showUserModal = false" class="close-btn">×</button>
        </div>
        <form @submit.prevent="saveUser" class="modal-form">
          <div class="form-row">
            <div class="form-group">
              <label>登录名</label>
              <input v-model="userForm.username" type="text" placeholder="用于系统登录" required :disabled="!!editingUser" />
            </div>
            <div class="form-group">
              <label>用户真实姓名</label>
              <input v-model="userForm.full_name" type="text" placeholder="显示名称" required />
            </div>
          </div>
          
          <div v-if="!editingUser" class="form-group">
            <label>登录密码</label>
            <input v-model="userForm.password" type="text" readonly />
            <p class="field-hint">新建员工默认密码为 123456，创建后可通过“修改密码”单独调整。</p>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>所属分公司</label>
              <select v-model="userForm.branch_id" @change="userForm.department_id = null" required>
                <option :value="null">请选择分公司</option>
                <option v-for="b in structure" :key="b.id" :value="b.id">{{ b.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>所属部门</label>
              <select v-model="userForm.department_id" required>
                <option :value="null">请选择部门</option>
                <option v-for="d in availableDepartments" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>账号角色</label>
            <select v-model="userForm.role" @change="handleRoleChange" required>
              <option value="employee">普通员工 (Employee)</option>
              <option value="staff_admin">普通管理员 (Staff Admin)</option>
              <option value="daily_admin">日常管理员 (Daily Admin)</option>
              <option value="executive">高管 (Executive)</option>
              <option value="owner">老板 (Owner)</option>
            </select>
            <p v-if="userForm.role === 'owner' || userForm.role === 'super_admin'" class="role-hint">老板/超级管理员拥有全量上帝权限，无需勾选下方权限位。</p>
          </div>

          <!-- Permissions Section -->
          <div v-if="userForm.role !== 'owner' && userForm.role !== 'super_admin'" class="permissions-section">
            <label class="section-label">功能权限设置 (可自由组合)</label>
            <div class="permissions-grid">
              <div v-for="p in permissionOptions" :key="p.value" class="permission-item">
                <input type="checkbox" :id="'perm_' + p.value" :value="p.value" v-model="userForm.permissions" />
                <label :for="'perm_' + p.value">
                  <span class="p-name">{{ p.label }}</span>
                  <span class="p-desc">{{ p.desc }}</span>
                </label>
              </div>
            </div>
          </div>

          <div class="form-group checkbox">
            <input type="checkbox" id="is_active" v-model="userForm.is_active" />
            <label for="is_active">启用该账号</label>
          </div>

          <div class="modal-footer">
            <button type="button" @click="showUserModal = false" class="btn-secondary">取消</button>
            <button type="submit" class="btn-primary" :disabled="saving">
              {{ saving ? '保存中...' : '提交保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Organization Management Modal -->
    <div v-if="showOrgModal" class="modal-overlay" @click.self="showOrgModal = false">
      <div class="modal-card wide glass-panel">
        <div class="modal-header">
          <h3>组织架构管理</h3>
          <button @click="showOrgModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-body org-manager">
          <div class="org-column">
            <h4>分公司列表</h4>
            <div class="org-list">
              <div v-for="b in structure" :key="b.id" :class="['org-item', { active: selectedBranch?.id === b.id }]" @click="selectedBranch = b">
                {{ b.name }}
              </div>
            </div>
            <div class="org-add">
              <input v-model="newBranchName" type="text" placeholder="新分公司名称" />
              <button @click="handleAddBranch" class="btn-sm">添加</button>
            </div>
          </div>

          <div class="org-column" v-if="selectedBranch">
            <h4>【{{ selectedBranch.name }}】下属部门</h4>
            <div class="org-list">
              <div v-for="d in selectedBranch.departments" :key="d.id" class="org-item no-hover">
                {{ d.name }}
              </div>
            </div>
            <div class="org-add">
              <input v-model="newDeptName" type="text" placeholder="新部门名称" />
              <button @click="handleAddDept" class="btn-sm">添加</button>
            </div>
          </div>
          <div class="org-empty" v-else>
            请在左侧选择分公司以管理部门
          </div>
        </div>
      </div>
    </div>

    <!-- Role Templates Management Modal -->
    <div v-if="showTemplateModal" class="modal-overlay" @click.self="showTemplateModal = false">
      <div class="modal-card wide glass-panel">
        <div class="modal-header">
          <h3>角色权限模板设置</h3>
          <button @click="showTemplateModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-body template-manager">
          <div v-if="templates.length === 0" class="loading-state">
             正在加载角色模板...
          </div>
          <template v-else>
            <div class="template-tabs">
              <button v-for="t in templates" :key="t.role" :class="['tab-btn', { active: activeTemplateTab === t.role }]" @click="activeTemplateTab = t.role">
                {{ roleMap[t.role] }}
              </button>
            </div>
            
            <div v-if="currentTemplate" class="template-content">
              <div class="form-group">
                <label>模板描述</label>
                <input v-model="currentTemplate.description" type="text" placeholder="例如：负责日常业务操作的职员" />
              </div>
              
              <label class="section-label">默认勾选权限位</label>
              <div class="permissions-grid">
                 <div v-for="p in permissionOptions" :key="p.value" class="permission-item">
                  <input type="checkbox" :id="'t_perm_' + p.value" :value="p.value" v-model="currentTemplate.permissions" />
                  <label :for="'t_perm_' + p.value">
                    <span class="p-name">{{ p.label }}</span>
                    <span class="p-desc">{{ p.desc }}</span>
                  </label>
                </div>
              </div>
            </div>
          </template>
        </div>
        <div class="modal-footer">
          <button @click="showTemplateModal = false" class="btn-secondary">关闭</button>
          <button @click="saveTemplates" class="btn-primary" :disabled="saving">
            {{ saving ? '正在保存...' : '保存模板设置' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showPasswordModal" class="modal-overlay" @click.self="closePasswordModal">
      <div class="modal-card modal-card-sm glass-panel">
        <div class="modal-header">
          <div>
            <h3>修改密码</h3>
            <p class="modal-subtitle">{{ passwordTargetUser?.full_name || passwordTargetUser?.username }}</p>
          </div>
          <button @click="closePasswordModal" class="close-btn">×</button>
        </div>
        <form @submit.prevent="submitPasswordChange" class="modal-form">
          <div class="form-group">
            <label>新密码</label>
            <input v-model="passwordForm.password" type="password" minlength="6" required />
          </div>
          <div class="form-group">
            <label>确认新密码</label>
            <input v-model="passwordForm.confirm_password" type="password" minlength="6" required />
          </div>
          <div class="modal-footer">
            <button type="button" @click="closePasswordModal" class="btn-secondary">取消</button>
            <button type="submit" class="btn-primary" :disabled="saving">
              {{ saving ? '保存中...' : '保存新密码' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../store/auth'
import { 
  Users as IconUsers, 
  Building as IconBuilding,
  Edit as IconEdit,
  KeyRound as IconKeyRound,
  Trash as IconTrash
} from 'lucide-vue-next'

const auth = useAuthStore()
const DEFAULT_PASSWORD = '123456'
const users = ref([])
const structure = ref([])
const templates = ref([])
const searchQuery = ref('')
const saving = ref(false)

// Role mappings
const roleMap = {
  'owner': '老板',
  'executive': '高管',
  'daily_admin': '日常管理员',
  'staff_admin': '普通管理员',
  'employee': '员工',
  'super_admin': '超级管理员'
}

// Permission Options
const permissionOptions = [
  { label: '员工管理', value: 'manage_staff', desc: '可新增/编辑员工账号及组织架构' },
  { label: '通知发布', value: 'edit_notices', desc: '可发布及编辑首页重要通知' },
  { label: '价格管理', value: 'edit_prices', desc: '可调整运费价格及相关参数' },
  { label: '案例编辑', value: 'edit_cases', desc: '可管理小易教练的实战案例' },
  { label: '参数设置', value: 'edit_settings', desc: '可调整 AI 温度、搜索深度等系统参数' },
  { label: '日志查看', value: 'view_logs', desc: '可查看所有用户的 AI 会话记录' },
  { label: '知识库管理', value: 'edit_knowledge', desc: '可上传及更新 RAG 知识库文档' }
]

// Default Role Permissions Matrix (Fallback if dynamic templates fail)
const fallbackRoleMatrix = {
  'employee': [],
  'staff_admin': ['manage_staff'],
  'daily_admin': ['manage_staff', 'edit_notices', 'edit_prices', 'edit_cases', 'edit_settings', 'edit_knowledge'],
  'executive': ['edit_notices', 'edit_prices', 'edit_cases', 'view_logs', 'edit_settings', 'edit_knowledge'],
  'owner': ['manage_staff', 'edit_notices', 'edit_prices', 'edit_cases', 'edit_settings', 'view_logs', 'edit_knowledge']
}

// Fetch Data
const fetchData = async () => {
  try {
    const [uRes, sRes, tRes] = await Promise.all([
      axios.get('/api/staff/users'),
      axios.get('/api/staff/structure'),
      axios.get('/api/staff/role-templates')
    ])
    users.value = uRes.data
    structure.value = sRes.data
    templates.value = tRes.data
  } catch (err) {
    console.error("Failed to load staff data", err)
    // 如果后端模板拉取失败，至少确保 templates 里有 fallback，不至于显示加载中
    if (templates.value.length === 0) {
      templates.value = Object.keys(fallbackRoleMatrix).map(role => ({
        role,
        permissions: fallbackRoleMatrix[role],
        description: '系统预设权限'
      }))
    }
  }
}

onMounted(fetchData)

// Table Filtering
const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  const q = searchQuery.value.toLowerCase()
  return users.value.filter(u => 
    u.username.toLowerCase().includes(q) || 
    (u.branch && u.branch.toLowerCase().includes(q))
  )
})

// User Modal Logic
const showUserModal = ref(false)
const editingUser = ref(null)
const userForm = ref({
  username: '',
  full_name: '',
  password: DEFAULT_PASSWORD,
  role: 'employee',
  permissions: [],
  branch_id: null,
  department_id: null,
  is_active: true
})

const handleRoleChange = () => {
  // 优先从后端加载的模板中查找权限
  const template = templates.value.find(t => t.role === userForm.value.role)
  if (template) {
    userForm.value.permissions = [...template.permissions]
  } else if (fallbackRoleMatrix[userForm.value.role]) {
    userForm.value.permissions = [...fallbackRoleMatrix[userForm.value.role]]
  }
}

const availableDepartments = computed(() => {
  if (!userForm.value.branch_id) return []
  const branch = structure.value.find(b => b.id === userForm.value.branch_id)
  return branch ? branch.departments : []
})

const openUserModal = (user) => {
  if (user) {
    editingUser.value = user
    userForm.value = {
      username: user.username,
      full_name: user.full_name || '',
      password: '',
      role: user.role,
      permissions: user.permissions || [],
      branch_id: user.branch_id,
      department_id: user.department_id,
      is_active: user.is_active
    }
  } else {
    editingUser.value = null
    userForm.value = {
      username: '',
      full_name: '',
      password: DEFAULT_PASSWORD,
      role: 'employee',
      permissions: [],
      branch_id: auth.user?.branch_id || null, // 默认带出自己的分公司
      department_id: null,
      is_active: true
    }
  }
  showUserModal.value = true
}

const saveUser = async () => {
  saving.value = true
  try {
    if (editingUser.value) {
      await axios.patch(`/api/staff/users/${editingUser.value.id}`, userForm.value)
    } else {
      await axios.post('/api/staff/users', {
        ...userForm.value,
        password: userForm.value.password || DEFAULT_PASSWORD,
      })
    }
    showUserModal.value = false
    fetchData()
  } catch (err) {
    alert(err.response?.data?.detail || "操作失败")
  } finally {
    saving.value = false
  }
}

const showPasswordModal = ref(false)
const passwordTargetUser = ref(null)
const passwordForm = ref({
  password: '',
  confirm_password: '',
})

const openPasswordModal = (user) => {
  passwordTargetUser.value = user
  passwordForm.value = {
    password: '',
    confirm_password: '',
  }
  showPasswordModal.value = true
}

const closePasswordModal = () => {
  showPasswordModal.value = false
  passwordTargetUser.value = null
  passwordForm.value = {
    password: '',
    confirm_password: '',
  }
}

const submitPasswordChange = async () => {
  if (!passwordTargetUser.value) return
  if (passwordForm.value.password !== passwordForm.value.confirm_password) {
    alert('两次输入的密码不一致')
    return
  }

  saving.value = true
  try {
    await axios.patch(`/api/staff/users/${passwordTargetUser.value.id}/password`, passwordForm.value)
    closePasswordModal()
    alert('密码修改成功')
  } catch (err) {
    alert(err.response?.data?.detail || '密码修改失败')
  } finally {
    saving.value = false
  }
}

const handleDeleteUser = async (user) => {
  if (!confirm(`确定要永久删除账号 ${user.username} (${user.full_name}) 吗？`)) return
  try {
    await axios.delete(`/api/staff/users/${user.id}`)
    fetchData()
  } catch (err) {
    alert(err.response?.data?.detail || "删除失败")
  }
}

// Excel Logic
const importInput = ref(null)
const triggerImport = () => importInput.value.click()

const handleExport = async () => {
  try {
    const response = await axios.get('/api/staff/users/export', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', '员工账号导出.xlsx')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (err) {
    console.error("Export failed", err)
    alert("导出失败")
  }
}

const handleImport = async (e) => {
  const file = e.target.files[0]
  if (!file) return
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const res = await axios.post('/api/staff/users/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    let msg = res.data.message
    if (res.data.errors && res.data.errors.length > 0) {
      msg += "\n\n部分导入失败:\n" + res.data.errors.join("\n")
    }
    alert(msg)
    fetchData()
  } catch (err) {
    alert(err.response?.data?.detail || "导入失败")
  } finally {
    e.target.value = ''
  }
}

// Org Management Modal Logic
const showOrgModal = ref(false)
const selectedBranch = ref(null)
const newBranchName = ref('')
const newDeptName = ref('')

const openOrgModal = () => {
  showOrgModal.value = true
  selectedBranch.value = structure.value[0] || null
}

const handleAddBranch = async () => {
  if (!newBranchName.value) return
  try {
    await axios.post('/api/staff/branches', { name: newBranchName.value })
    newBranchName.value = ''
    fetchData() // Refresh structure
  } catch (err) {
    alert("添加分公司失败")
  }
}

const handleAddDept = async () => {
  if (!newDeptName.value || !selectedBranch.value) return
  try {
    await axios.post('/api/staff/departments', { 
      name: newDeptName.value, 
      branch_id: selectedBranch.value.id 
    })
    newDeptName.value = ''
    fetchData() // Refresh structure
  } catch (err) {
    alert("添加部门失败")
  }
}
// Role Template Modal Logic
const showTemplateModal = ref(false)
const activeTemplateTab = ref('employee')

const openTemplateModal = () => {
  if (templates.value.length > 0) {
    activeTemplateTab.value = templates.value[0]?.role
  } else {
    activeTemplateTab.value = 'employee'
    fetchData() // 再次尝试获取
  }
  showTemplateModal.value = true
}

const currentTemplate = computed(() => {
  return templates.value.find(t => t.role === activeTemplateTab.value)
})

const saveTemplates = async () => {
  saving.value = true
  try {
    await axios.patch('/api/staff/role-templates', templates.value)
    alert("模板已成功更新")
    showTemplateModal.value = false
  } catch (err) {
    alert("保存模板失败")
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.staff-container {
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
  height: 100vh;
  overflow-y: auto;
}

.staff-header {
  padding: 24px 32px;
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left h1 {
  font-size: 24px;
  margin-top: 8px;
}

.back-link {
  font-size: 14px;
  color: var(--text-secondary);
  text-decoration: none;
}

.header-right {
  display: flex;
  gap: 12px;
}

.staff-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.summary-card {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.card-icon.blue { background: rgba(37, 99, 235, 0.1); color: #2563eb; }
.card-icon.purple { background: rgba(124, 58, 237, 0.1); color: #7c3aed; }

.card-info .label {
  display: block;
  font-size: 14px;
  color: var(--text-secondary);
}

.card-info .value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.table-container {
  padding: 24px;
}

.table-scroll {
  max-height: min(62vh, calc(100vh - 320px));
  overflow: auto;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.search-input {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  width: 240px;
  background: rgba(255,255,255,0.05);
}

.staff-table {
  width: 100%;
  border-collapse: collapse;
}

.staff-table th {
  text-align: left;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 14px;
}

.staff-table td {
  padding: 16px;
  border-bottom: 1px solid rgba(0,0,0,0.03);
  font-size: 14px;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar-small {
  width: 32px;
  height: 32px;
  background: var(--primary-gradient);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 700;
}

.role-tag {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.role-tag.super_admin, .role-tag.owner { background: rgba(124, 58, 237, 0.1); color: #7c3aed; }
.role-tag.executive { background: rgba(37, 99, 235, 0.1); color: #2563eb; }
.role-tag.daily_admin { background: rgba(16, 185, 129, 0.1); color: #059669; }
.role-tag.staff_admin { background: rgba(245, 158, 11, 0.1); color: #d97706; }
.role-tag.employee { background: rgba(148, 163, 184, 0.1); color: #64748b; }

/* Permissions Section Styles */
.permissions-section {
  margin-top: 10px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px dashed var(--border-color);
}

.section-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
  display: block;
}

.permissions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.permission-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.permission-item:hover {
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.permission-item input {
  margin-top: 4px;
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.permission-item label {
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.p-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.p-desc {
  font-size: 11px;
  color: var(--text-secondary);
}

.role-hint {
  font-size: 12px;
  color: #7c3aed;
  margin-top: 4px;
  font-weight: 500;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cbd5e1;
  margin-right: 6px;
}
.status-dot.active { background: #10b981; }

.icon-btn {
  padding: 6px;
  border-radius: 6px;
  color: var(--text-secondary);
}
.icon-btn:hover { background: rgba(0,0,0,0.05); }
.icon-btn.edit:hover { color: #2563eb; }
.icon-btn.password:hover { color: #7c3aed; }
.icon-btn.delete:hover { color: #ef4444; }

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  width: 580px;
  padding: 32px;
  background: white;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-card-sm { width: 420px; }
.modal-card.wide { width: 800px; }

.modal-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.close-btn { font-size: 24px; color: var(--text-secondary); }

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.field-hint {
  font-size: 12px;
  color: var(--text-secondary);
}

input, select {
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  background: white;
}

.checkbox {
  flex-direction: row;
  align-items: center;
  gap: 10px;
}

.checkbox label { margin: 0; }

.modal-footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* Org Manager Styles */
.org-manager {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  min-height: 300px;
}

.org-column h4 {
  margin-bottom: 16px;
  font-size: 14px;
  color: var(--text-secondary);
}

.org-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 240px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 8px;
  margin-bottom: 16px;
}

.org-item {
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.org-item:hover { background: rgba(0,0,0,0.03); }
.org-item.active { background: rgba(37, 99, 235, 0.1); color: #2563eb; font-weight: 600; }
.org-item.no-hover { cursor: default; }
.org-item.no-hover:hover { background: none; }

.org-add {
  display: flex;
  gap: 8px;
}

.btn-sm {
  padding: 8px 12px;
  background: #f1f5f9;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.org-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 14px;
  background: rgba(0,0,0,0.02);
  border-radius: 8px;
}

.btn-secondary {
  padding: 10px 20px;
  background: #f1f5f9;
  color: #475569;
  border-radius: 8px;
  font-weight: 600;
}

.btn-outline {
  padding: 10px 20px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
}
.template-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
  min-height: 42px;
}

.tab-btn {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: #f1f5f9;
}

.tab-btn.active {
  background: var(--primary-light);
  color: var(--primary-color);
  border-color: var(--primary-color);
}

.template-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.loading-state {
  padding: 40px;
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
}
</style>
