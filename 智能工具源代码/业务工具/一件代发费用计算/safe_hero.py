import re

file_path = r'd:\Antigravity-work\Projects\Dev-Forge\一件代发费用计算\美国一件代发报价计算器.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_hero = '''        <div class="hero-text">
          <div class="eyebrow">ZYD USA WAREHOUSE</div>
          <h1>一件代发报价工具</h1>'''

new_hero = '''        <div class="hero-text">
          <div class="hero-brand" style="display: flex; align-items: flex-start; gap: 20px; margin-bottom: 24px;">
            <img src="仲易达供应链LOGO.png" alt="ZYD" style="height: 60px; object-fit: contain;">
            <div>
              <div class="eyebrow" style="margin-bottom: 4px;">ZYD USA WAREHOUSE</div>
              <h1 style="font-size: 36px; line-height: 1.1; margin: 0;">一件代发报价工具</h1>
            </div>
          </div>'''

content = content.replace(old_hero, new_hero)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Applied safe hero logo injection.')
