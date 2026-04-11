import re

file_path = r'd:\Antigravity-work\Projects\Dev-Forge\一件代发费用计算\美国一件代发报价计算器.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Clean up duplicate totals-grid elements
stray_totals_pattern = r'</div>\s*<div class="metric-card"><span class="meta-label">单件均摊</span><strong id="unitCostView">\$0\.00</strong></div>\s*<div class="metric-card"><span class="meta-label">最高命中档位</span><strong id="matchedBracketView">-</strong></div>\s*</div>'
content = re.sub(stray_totals_pattern, '</div>', content)

# 2. Clean up duplicate customer quote grand total
stray_quote_grand = r'</div>\s*<div class="customer-meta-card">\s*<span class="meta-label">总报价</span>\s*<strong id="customerQuoteGrandTotal">\$0\.00</strong>\s*</div>\s*</div>'
content = re.sub(stray_quote_grand, '</div>', content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
