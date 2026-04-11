import re

file_path = r'd:\Antigravity-work\Projects\Dev-Forge\一件代发费用计算\美国一件代发报价计算器.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Targeted CSS update for buttons - THE "DA QI" VERSION
old_actions_css = r'\.quote-actions\s*\{\s*display:\s*flex;\s*flex-direction:\s*column;\s*gap:\s*12px;\s*margin-top:\s*32px;\s*\}'
new_actions_css = """      .quote-actions {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-top: 32px;
        border-top: 1px solid var(--line);
        padding-top: 24px;
      }
      .quote-actions .button {
        width: 100%;
        padding: 16px;
        font-size: 16px;
        background: var(--accent);
        color: #fff;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 700;
        box-shadow: 0 4px 10px rgba(208, 80, 0, 0.2);
        transition: all 0.2s;
      }
      .quote-actions .button:hover { background: var(--accent-hover); transform: translateY(-1px); }
      .quote-actions .action-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
      }
      .quote-actions .action-row .button-secondary {
        padding: 14px;
        background: #fff;
        border: 1px solid #D1D5DB;
        color: #374151;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.2s;
      }
      .quote-actions .action-row .button-secondary:hover { background: #f9fafb; border-color: #9ca3af; }"""

content = re.sub(old_actions_css, new_actions_css, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Applied DA QI button styles.')
