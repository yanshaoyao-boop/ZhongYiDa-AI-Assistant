const path = require('node:path')
const { pathToFileURL } = require('node:url')

async function main() {
  const markdownModuleUrl = pathToFileURL(
    path.join(__dirname, '..', 'src', 'utils', 'markdown.js')
  ).href

  const { renderMarkdownToHtml } = await import(markdownModuleUrl)

  const markdownTable = [
    '| 渠道 | 价格 |',
    '| --- | --- |',
    '| 明日之星 | 12.5/kg |',
  ].join('\n')

  let html
  try {
    html = renderMarkdownToHtml(markdownTable)
  } catch (error) {
    throw new Error(`renderMarkdownToHtml should support tables without throwing: ${error.message}`)
  }

  if (!html.includes('chat-table-wrap')) {
    throw new Error('renderMarkdownToHtml should wrap tables in chat-table-wrap')
  }

  if (!html.includes('chat-markdown-table')) {
    throw new Error('renderMarkdownToHtml should add the chat-markdown-table class')
  }

  if (!html.includes('明日之星')) {
    throw new Error('renderMarkdownToHtml should keep table cell content intact')
  }

  console.log('renderMarkdownToHtml table runtime regression test passed')
}

main().catch((error) => {
  console.error(error.message || error)
  process.exit(1)
})
