const fs = require('node:fs')
const path = require('node:path')

const chatViewPath = path.join(__dirname, '..', 'src', 'views', 'ChatView.vue')
const intelPanelPath = path.join(__dirname, '..', 'src', 'views', 'chat', 'components', 'WebCombatIntelPanel.vue')
const mpChatPath = path.join(__dirname, '..', '..', 'frontend-uniapp', 'src', 'pages', 'chat', 'chat.vue')
const mpIntelPanelPath = path.join(__dirname, '..', '..', 'frontend-uniapp', 'src', 'pages', 'chat', 'components', 'CombatIntelPanel.vue')

const chatViewSource = fs.readFileSync(chatViewPath, 'utf8')
const intelPanelSource = fs.readFileSync(intelPanelPath, 'utf8')
const mpChatSource = fs.readFileSync(mpChatPath, 'utf8')
const mpIntelPanelSource = fs.readFileSync(mpIntelPanelPath, 'utf8')

const expectedSnippets = [
  [chatViewSource, '【结束对练】请现在切换为“资深销售总监/金牌导师”的人设，基于刚才的全部聊天记录输出结构化点评报告。', 'ChatView.vue should send the coach review trigger marker'],
  [intelPanelSource, '结束对练并评价', 'WebCombatIntelPanel.vue should use the new quit button copy'],
  [mpChatSource, '【结束对练】请现在切换为“资深销售总监/金牌导师”的人设，基于刚才的全部聊天记录输出结构化点评报告。', 'miniapp chat.vue should send the same coach review trigger marker'],
  [mpIntelPanelSource, '结束对练并评价', 'miniapp CombatIntelPanel.vue should use the new quit button copy'],
]

const missing = expectedSnippets
  .filter(([source, snippet]) => !source.includes(snippet))
  .map(([, , message]) => message)

const forbiddenSnippets = [
  [chatViewSource, '请针对刚才的对练表现进行深度点评和评分。请用 Markdown 格式输出。', 'ChatView.vue should no longer send the legacy review phrase'],
  [intelPanelSource, '结束对练并结算', 'WebCombatIntelPanel.vue should no longer show the settlement wording'],
  [mpChatSource, '请切换到资深销售总监视角的点评。请用 Markdown 输出。', 'miniapp chat.vue should no longer send the vague review phrase'],
]

const forbiddenHits = forbiddenSnippets
  .filter(([source, snippet]) => source.includes(snippet))
  .map(([, , message]) => message)

if (missing.length || forbiddenHits.length) {
  throw new Error(
    ['Coach review trigger snippets are incorrect:']
      .concat(missing)
      .concat(forbiddenHits)
      .join('\n')
  )
}

console.log('Coach review trigger snippets look correct for H5 and miniapp')
