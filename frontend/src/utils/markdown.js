import { marked } from 'marked'
import createDOMPurify from 'dompurify'

function escapeAttribute(value) {
    return String(value ?? '').replace(/&/g, '&amp;').replace(/"/g, '&quot;')
}

function resolvePurifier() {
    if (createDOMPurify && typeof createDOMPurify.sanitize === 'function') {
        return createDOMPurify
    }

    if (typeof window !== 'undefined' && typeof createDOMPurify === 'function') {
        try {
            return createDOMPurify(window)
        } catch (error) {
            console.warn('Failed to initialize DOMPurify with window, falling back to passthrough sanitizer.', error)
        }
    }

    return {
        sanitize(dirty) {
            return String(dirty ?? '')
        },
    }
}

function renderInlineTokens(context, token) {
    if (context?.parser && Array.isArray(token?.tokens)) {
        return context.parser.parseInline(token.tokens)
    }
    return token?.text || ''
}

function renderTableCell(tagName, context, cell) {
    const align = cell?.align ? ` style="text-align:${escapeAttribute(cell.align)}"` : ''
    return `<${tagName}${align}>${renderInlineTokens(context, cell)}</${tagName}>`
}

const DOMPurify = resolvePurifier()

const renderer = new marked.Renderer()
renderer.table = function (token) {
    const headerHtml = (token.header || [])
        .map((cell) => renderTableCell('th', this, cell))
        .join('')
    const rowsHtml = (token.rows || [])
        .map((row) => `<tr>${row.map((cell) => renderTableCell('td', this, cell)).join('')}</tr>`)
        .join('')

    return `
    <div class="chat-table-wrap">
        <table class="chat-markdown-table">
            <thead><tr>${headerHtml}</tr></thead>
            <tbody>${rowsHtml}</tbody>
        </table>
    </div>
    `
}

// Render markdown headings as bold paragraphs to avoid font-size jumps.
renderer.heading = function (token) {
    return `<p class="chat-heading"><strong>${renderInlineTokens(this, token)}</strong></p>\n`
}

marked.setOptions({
    breaks: true,
    gfm: true,
    renderer,
})

function normalizeInlineListMarkers(text) {
    if (!text) return ''

    let normalized = String(text).replace(/\r\n?/g, '\n')

    // Collapse duplicated ordered-list markers at the start of a line:
    // "1. 1. Item" -> "1. Item"
    normalized = normalized.replace(
        /(^|\n)(\s*)((?:\d{1,2}|[A-H])[.)])(?:\s+\3)+(?=\s+)/g,
        '$1$2$3'
    )

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
