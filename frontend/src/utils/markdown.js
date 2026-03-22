import { marked } from 'marked'
import DOMPurify from 'dompurify'

const renderer = new marked.Renderer()

renderer.table = function (token) {
    const html = marked.Renderer.prototype.table.call(this, token)
    return `
    <div class="chat-table-wrap">
        ${html.replace('<table>', '<table class="chat-markdown-table">')}
    </div>
    `
}

// 统一配置
marked.setOptions({
    breaks: true,
    gfm: true,
    renderer,
})

/**
 * 安全渲染 Markdown 为 HTML
 * @param {string} text - 原始 Markdown 文本
 * @returns {string} - 消毒后的 HTML
 */
export function renderMarkdownToHtml(text) {
    if (!text) return ''
    // 移除可能导致 marked 解析异常的打字机符号
    let cleaned = text.replace(/~~([\s\S]*?)~~/g, '$1')
    cleaned = cleaned.replace(/~+/g, '')
    return marked.parse(cleaned)
}

export function renderMarkdown(text) {
    return DOMPurify.sanitize(renderMarkdownToHtml(text))
}
