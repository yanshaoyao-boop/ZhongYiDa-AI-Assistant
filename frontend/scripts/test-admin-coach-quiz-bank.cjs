const fs = require('node:fs')
const path = require('node:path')

const source = fs.readFileSync(path.join(__dirname, '..', 'src', 'views', 'AdminView.vue'), 'utf8')

const requiredSnippets = [
  '教练出题题库',
  'quizQuestions',
  'quizFiles',
  'uploadQuizBank',
  'fetchQuizQuestions',
  '/api/coach-quiz/bank',
  'deleteQuizQuestion',
]

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet))

if (missing.length > 0) {
  throw new Error(`AdminView coach quiz bank is missing required snippets:\n${missing.join('\n')}`)
}

console.log('admin coach quiz bank snippets look correct')
