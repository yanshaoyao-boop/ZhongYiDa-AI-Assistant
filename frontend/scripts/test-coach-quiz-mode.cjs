const fs = require('node:fs')
const path = require('node:path')

const source = fs.readFileSync(path.join(__dirname, '..', 'src', 'views', 'ChatView.vue'), 'utf8')

const requiredSnippets = [
  '教练出题',
  '教练对练',
  'quizQuestionCounts',
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
  throw new Error(`ChatView coach quiz mode is missing required snippets:\n${missing.join('\n')}`)
}

console.log('coach quiz mode snippets look correct')
