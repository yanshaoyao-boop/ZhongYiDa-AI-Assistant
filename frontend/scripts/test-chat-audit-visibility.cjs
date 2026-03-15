const fs = require('node:fs')
const path = require('node:path')

const authSource = fs.readFileSync(path.join(__dirname, '..', 'src', 'store', 'auth.js'), 'utf8')
const routerSource = fs.readFileSync(path.join(__dirname, '..', 'src', 'router', 'index.js'), 'utf8')
const adminViewSource = fs.readFileSync(path.join(__dirname, '..', 'src', 'views', 'AdminView.vue'), 'utf8')

const requiredSnippets = [
  "canViewChatAudit: (state) => ['owner', 'executive', 'super_admin'].includes(state.user?.role)",
  "v-if=\"auth.canViewChatAudit\"",
  "to.meta.requiresChatAudit && !auth.canViewChatAudit",
]

for (const snippet of requiredSnippets) {
  if (!authSource.includes(snippet) && !routerSource.includes(snippet) && !adminViewSource.includes(snippet)) {
    throw new Error(`Missing chat audit visibility snippet: ${snippet}`)
  }
}

if (!routerSource.includes("path: '/admin/chat-logs'") || !routerSource.includes("meta: { requiresAuth: true, requiresAdmin: true, requiresChatAudit: true }")) {
  throw new Error('Chat audit route is missing the dedicated requiresChatAudit flag')
}

if (!routerSource.includes("path: '/admin'") || !routerSource.includes("meta: { requiresAuth: true, requiresAdmin: true }")) {
  throw new Error('Admin home route should remain visible to all admin roles')
}

console.log('chat audit visibility looks correct')
