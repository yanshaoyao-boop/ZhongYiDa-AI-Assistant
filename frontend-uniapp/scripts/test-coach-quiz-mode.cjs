const fs = require('node:fs')
const path = require('node:path')

const source = fs.readFileSync(path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'), 'utf8')

const requiredSnippets = [
  '教练出题',
  'coachQuizQuestionCounts',
  'startCoachQuizSession',
  'coachQuizSession',
  'coach-quiz-card',
  'coach-quiz-option',
  'nextCoachQuizQuestion',
  'coach-quiz-summary',
  'isCoachQuizActive',
]

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet))

if (missing.length > 0) {
  throw new Error(`miniapp chat coach quiz mode is missing required snippets:\n${missing.join('\n')}`)
}

console.log('miniapp coach quiz mode snippets look correct')
