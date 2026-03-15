const fs = require('node:fs')
const path = require('node:path')

const filePath = path.join(__dirname, '..', 'src', 'views', 'ToolsView.vue')
const source = fs.readFileSync(filePath, 'utf8')

if (source.includes('window.location.href = runtimePath')) {
  throw new Error('ToolsView fallback navigation still forces the current tab to jump into the tool page.')
}

if (!source.includes('link.target = \'_blank\'')) {
  throw new Error('ToolsView is expected to open tool pages through a dedicated new-tab link flow.')
}

console.log('tools open behavior looks correct')
