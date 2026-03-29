import { marked } from 'marked'
import DOMPurify from 'dompurify'

const renderer = new marked.Renderer()
const defaultRenderer = new marked.Renderer()

renderer.table = (token) => {
    const html = defaultRenderer.table(token)
    return `
    <div class="chat-table-wrap">
        ${html.replace('<table>', '<table class="chat-markdown-table">')}
    </div>
    `
}

// Render markdown headings as bold paragraphs to avoid font-size jumps.
renderer.heading = (token) => {
    const html = defaultRenderer.heading(token)
    return html.replace(
        /^<h[1-6][^>]*>([\s\S]*?)<\/h[1-6]>\n?$/,
        '<p class="chat-heading"><strong>$1</strong></p>\n'
    )
}

marked.setOptions({
    breaks: true,
    gfm: true,
    renderer,
})

function normalizeInlineListMarkers(text) {
    if (!text) return ''

    let normalized = String(text).replace(/\r\n?/g, '\n')

    // Ensure one space after list markers: "1.xxx" -> "1. xxx"
    normalized = normalized.replace(
        /(^|\n)(\s*(?:\d{1,2}|[A-H])[.)])(?=\S)/g,
        '$1$2 '
    )

    // Split inline points into independent lines.
    normalized = normalized.replace(
        /([^\n])\s+((?:\d{1,2}|[A-H])[.)]\s+)/g,
        (match, prevChar, marker) => {
            if (/\d/.test(prevChar) && /^\d+\./.test(marker)) {
                return match
            }
            return `${prevChar}\n${marker}`
        }
    )

    return normalized
}

function emphasizeKeyLabels(text) {
    const keyLabels = [
        '\\u6838\\u5fc3\\u7ed3\\u8bba', // 核心结论
        '\\u5173\\u952e\\u70b9', // 关键点
        '\\u91cd\\u70b9', // 重点
        '\\u91cd\\u8981', // 重要
        '\\u6ce8\\u610f\\u4e8b\\u9879', // 注意事项
        '\\u98ce\\u9669\\u63d0\\u793a', // 风险提示
        '\\u884c\\u52a8\\u5efa\\u8bae', // 行动建议
        '\\u5efa\\u8bae', // 建议
        '\\u7ed3\\u8bba', // 结论
    ]
    const pattern = new RegExp(`(^|\\n)\\s*(${keyLabels.join('|')})([:\\uFF1A])`, 'g')
    return String(text || '').replace(pattern, '$1<strong>$2$3</strong>')
}

export function renderMarkdownToHtml(text) {
    if (!text) return ''
    let cleaned = text.replace(/~~([\s\S]*?)~~/g, '$1')
    cleaned = cleaned.replace(/~+/g, '')
    cleaned = emphasizeKeyLabels(cleaned)
    cleaned = normalizeInlineListMarkers(cleaned)
    return marked.parse(cleaned)
}

export function renderMarkdown(text) {
    return DOMPurify.sanitize(renderMarkdownToHtml(text))
}
