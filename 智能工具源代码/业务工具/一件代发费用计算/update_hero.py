import re

file_path = r'd:\Antigravity-work\Projects\Dev-Forge\一件代发费用计算\美国一件代发报价计算器.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Hero HTML to include logo
new_hero_inner = """        <div class="hero-text">
          <div class="hero-brand">
             <img src="仲易达供应链LOGO.png" alt="Logo" class="hero-logo" onerror="this.style.display='none'">
             <div class="hero-titles">
                <div class="eyebrow">ZYD USA WAREHOUSE</div>
                <h1>一件代发报价工具</h1>
             </div>
          </div>
          <p>录入包裹的装箱尺寸与业务模式，系统自动换算材积重与计费档位，输出财务明细账单，并一键出具标准商务对客报价单。</p>
        </div>"""
content = re.sub(r'<div class="hero-text">.*?</div>', new_hero_inner, content, flags=re.DOTALL)

# 2. Add styles for hero logo and resize h1
hero_styles_to_add = """
      .hero-brand { display: flex; align-items: center; gap: 20px; margin-bottom: 8px; }
      .hero-logo { height: 48px; width: auto; object-fit: contain; }
      .hero-titles h1 { font-size: 28px; margin-top: 2px; }
      .hero-titles .eyebrow { margin-bottom: 0; line-height: 1; }
"""

# Insert styles before </style>
content = content.replace('    </style>', hero_styles_to_add + '\n    </style>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated Hero section with logo and smaller title.')
