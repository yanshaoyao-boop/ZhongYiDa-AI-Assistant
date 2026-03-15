const fs = require('node:fs')
const path = require('node:path')

const source = fs.readFileSync(path.resolve(__dirname, '..', 'src', 'pages', 'admin', 'admin.vue'), 'utf8')

const requiredSnippets = [
  '教练出题题库',
  'quizQuestions',
  'selectAndUploadQuizBank',
  'fetchQuizQuestions',
  '/api/coach-quiz/bank',
  'deleteQuizQuestion',
]

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet))

if (missing.length > 0) {
  throw new Error(`miniapp admin coach quiz bank is missing required snippets:\n${missing.join('\n')}`)
}

console.log('miniapp admin coach quiz bank snippets look correct')
