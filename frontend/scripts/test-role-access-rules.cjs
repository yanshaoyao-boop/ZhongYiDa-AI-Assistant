const fs = require('node:fs')
const path = require('node:path')

const authSource = fs.readFileSync(path.join(__dirname, '..', 'src', 'store', 'auth.js'), 'utf8')
const staffViewSource = fs.readFileSync(path.join(__dirname, '..', 'src', 'views', 'StaffView.vue'), 'utf8')

const requiredSnippets = [
  "canViewChatAudit: (state) => ['owner', 'executive', 'super_admin'].includes(state.user?.role)",
  "canManageAllBranches: (state) => ['owner', 'super_admin', 'daily_admin'].includes(state.user?.role)",
  "v-if=\"auth.canManageAllBranches\"",
  "auth.canManageAllBranches ? '新增员工' : '新增本分公司员工'",
  "'daily_admin': ['manage_staff', 'edit_notices', 'edit_prices', 'edit_cases', 'edit_settings', 'edit_knowledge']",
]

for (const snippet of requiredSnippets) {
  if (!authSource.includes(snippet) && !staffViewSource.includes(snippet)) {
    throw new Error(`Missing role access rule snippet: ${snippet}`)
  }
}

console.log('role access rules look correct')
