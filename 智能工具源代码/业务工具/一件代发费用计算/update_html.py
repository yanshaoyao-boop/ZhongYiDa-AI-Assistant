import re

file_path = 'd:\\Antigravity-work\\Projects\\Dev-Forge\\一件代发费用计算\\美国一件代发报价计算器.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_css = """      :root {
        --bg: #F8F9FA;
        --paper: #FFFFFF;
        --paper-dark: #1E1E1E;
        --ink: #1A1B1E;
        --muted: #6B7280;
        --line: #E5E7EB;
        --accent: #D05000;
        --accent-hover: #A03D00;
        --accent-soft: rgba(208, 80, 0, 0.08);
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
        --shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.05);
        --shadow-lg: 0 20px 25px -5px rgba(0,0,0,0.05), 0 8px 10px -6px rgba(0,0,0,0.01);
        --radius: 12px;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: 'Inter', 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
        color: var(--ink);
        background: var(--bg);
        -webkit-font-smoothing: antialiased;
      }
      .page { max-width: 1480px; margin: 0 auto; padding: 32px; }
      .hero { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 32px; align-items: end; margin-bottom: 32px; }
      .hero-text { max-width: 720px; }
      .eyebrow, .meta-label, .field label, .section-title, th { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }
      .eyebrow { color: var(--accent); margin-bottom: 8px; display: inline-block; }
      h1 { margin: 0; font-size: clamp(32px, 5vw, 48px); font-weight: 800; line-height: 1.1; letter-spacing: -0.02em; color: #111827; }
      .hero-text p { margin: 12px 0 0; color: var(--muted); line-height: 1.6; font-size: 16px; }
      
      .hero-stat { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; padding: 24px 32px; background: #FFFFFF; border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow-sm); }
      .hero-stat > div { display: flex; flex-direction: column; gap: 8px; }
      .hero-stat strong { font-size: 28px; font-weight: 700; color: #111827; }
      #heroGrandTotal { color: var(--accent); }

      .workspace { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(420px, 0.45fr); gap: 32px; align-items: start; }
      
      .panel { background: var(--paper); border-radius: var(--radius); border: 1px solid var(--line); box-shadow: var(--shadow); }
      .panel.form { padding: 32px; }
      .panel.result { padding: 32px; position: sticky; top: 32px; background: #FFF; border: 1px solid var(--line); box-shadow: var(--shadow-lg); }
      
      .section-header { margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--line); }
      .section-header .section-title { font-size: 15px; color: #111827; }
      .section-header p { margin: 8px 0 0; color: var(--muted); font-size: 14px; line-height: 1.5; font-weight: 400; text-transform: none; letter-spacing: normal;}
      
      .quote-meta-block { margin-top: 32px; padding: 24px; background: #F8F9FA; border-radius: 8px; border: 1px dashed #D1D5DB; }
      .quote-meta-block .section-header { border-bottom: none; padding-bottom: 0; margin-bottom: 16px; }
      
      .form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; padding-top: 16px; }
      .field { display: grid; gap: 8px; }
      .field label { color: #374151; }
      .field input, .field select, .field textarea { 
        width: 100%; border: 1px solid var(--line); border-radius: 8px; background: #FFFFFF; 
        padding: 10px 14px; font-family: inherit; font-size: 15px; color: #111827; transition: all 0.2s;
      }
      .field input:focus, .field select:focus, .field textarea:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
      .field textarea { min-height: 80px; resize: vertical; }
      
      .toggle-row { display: flex; flex-wrap: wrap; gap: 24px; padding: 24px 0 12px; }
      .toggle-row label { display: inline-flex; align-items: center; gap: 8px; font-weight: 500; color: #374151; cursor: pointer; }
      .toggle-row input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--accent); }
      
      .box-group-block, .service-block { margin-top: 40px; }
      .box-group-list, .service-list { display: grid; gap: 16px; margin-top: 16px; }
      .box-group-row {
        display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)) auto;
        gap: 12px; align-items: end; padding: 16px;
        background: #FFFFFF; border: 1px solid var(--line); border-radius: 8px; box-shadow: var(--shadow-sm); transition: border-color 0.2s;
      }
      .box-group-row:hover { border-color: #D1D5DB; }
      .service-row { display: grid; grid-template-columns: minmax(0, 1.8fr) 120px auto auto; gap: 16px; align-items: end; margin-top: 16px; }
      
      .button, .button-secondary { 
        display: inline-flex; align-items: center; justify-content: center;
        border: 1px solid transparent; border-radius: 6px; padding: 10px 18px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; 
      }
      .button { background: var(--accent); color: #fff; box-shadow: var(--shadow-sm); }
      .button:hover { background: var(--accent-hover); }
      .button-secondary { background: #FFFFFF; color: #374151; border-color: #D1D5DB; box-shadow: var(--shadow-sm); }
      .button-secondary:hover { background: #F9FAFB; border-color: #9CA3AF; }
      .button-secondary.remove-box-group, .button-secondary.remove-service { padding: 10px; color: #EF4444; border-color: transparent; box-shadow: none; background: transparent; }
      .button-secondary.remove-box-group:hover, .button-secondary.remove-service:hover { background: #FEE2E2; }
      #addBoxGroupBtn, #addServiceBtn { margin-top: 16px; width: auto; background: var(--accent-soft); color: var(--accent); font-weight: 600; box-shadow: none; border-color: transparent; }
      #addBoxGroupBtn:hover, #addServiceBtn:hover { background: rgba(208,80,0,0.15); }
      
      .manual-chip, .tag { display: inline-flex; align-items: center; justify-content: center; border-radius: 4px; padding: 4px 8px; font-size: 12px; font-weight: 600; }
      .manual-chip { background: #FEE2E2; color: #991B1B; }
      .tag { background: #FEF3C7; color: #92400E; margin-left: 8px; }
      
      .metric-card { background: #F9FAFB; border: 1px solid var(--line); border-radius: 8px; padding: 16px; }
      .metric-card strong, .summary-grid strong, .totals-grid strong { display: block; margin-top: 8px; font-size: 20px; font-weight: 700; color: #111827; }
      
      .weight-grid, .summary-grid, .totals-grid { display: grid; gap: 16px; margin-top: 20px; }
      .weight-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
      .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .totals-grid { grid-template-columns: repeat(1, minmax(0, 1fr)); gap: 12px; }
      .totals-grid .metric-card { background: var(--accent-soft); border-color: transparent; position: relative; }
      .totals-grid .metric-card strong { font-size: 36px; color: var(--accent); }
      .totals-grid .metric-card-secondary { background: #F9FAFB; border: 1px solid var(--line); padding: 16px;}
      .totals-grid .metric-card-secondary strong { font-size: 20px; color: #111827; }
      .totals-secondary-row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 12px; }

      .table-wrap { margin-top: 24px; overflow: auto; border: 1px solid var(--line); border-radius: 8px; }
      table { width: 100%; border-collapse: collapse; text-align: left; background: #fff; }
      th, td { padding: 14px 16px; border-bottom: 1px solid var(--line); vertical-align: middle; }
      th { background: #F9FAFB; font-size: 12px; color: #6B7280; font-weight: 600; }
      td { font-size: 14px; color: #374151; }
      tbody tr:hover { background: #F9FAFB; }
      
      .manual-box { margin-top: 24px; padding: 16px; border-radius: 8px; background: #FFFBEB; border: 1px solid #FDE68A; }
      .manual-box .section-title { color: #92400E; margin-bottom: 8px; display: block; }
      .manual-box ul { margin: 8px 0 0; padding-left: 20px; color: #92400E; font-size: 14px; }
      .manual-box p { margin: 4px 0 0; color: #92400E; font-size: 14px; }
      
      .quote-actions { display: flex; flex-direction: column; gap: 12px; margin-top: 32px; border-top: 1px solid var(--line); padding-top: 24px;}
      .quote-actions .button { width: 100%; padding: 16px; font-size: 16px; }
      .quote-actions .action-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
      .quote-actions .action-row .button-secondary { padding: 14px; }
      
      /* Customer Quote Sheet */
      .customer-sheet {
        margin-top: 48px; padding: 48px; background: #FFFFFF; color: #111827;
        box-shadow: var(--shadow-lg); border: 1px solid var(--line); border-radius: var(--radius); position: relative;
      }
      .customer-sheet-head { display: flex; justify-content: space-between; gap: 32px; align-items: flex-start; padding-bottom: 32px; border-bottom: 2px solid #111827; }
      .customer-brand { display: flex; gap: 24px; align-items: center; }
      .logo-slot { height: 64px; display: flex; align-items: center; justify-content: flex-start; }
      .logo-slot img { height: 100%; max-width: 260px; object-fit: contain; display: block; }
      .logo-slot span { font-size: 16px; font-weight: 800; letter-spacing: 0.1em; color: #111827; border: 2px solid #111827; padding: 8px 16px; }
      .customer-brand-titles .eyebrow { color: var(--accent); margin-bottom: 4px; }
      .customer-brand-titles h2 { margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.02em; }
      
      .customer-sheet-head .quote-grand-block { text-align: right; }
      .quote-grand-block .meta-label { color: #6B7280; margin-bottom: 4px; display: block;}
      #customerQuoteGrandTotal { font-size: 36px; font-weight: 800; color: var(--accent); line-height: 1;}
      
      .customer-sheet-meta { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin-top: 24px; }
      .customer-meta-card { padding: 0; }
      .customer-meta-card strong { display: block; margin-top: 4px; font-size: 16px; font-weight: 600; color: #111827; }
      
      .customer-summary-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; margin-top: 32px; padding: 24px; background: #F9FAFB; border-radius: 8px; border: 1px solid var(--line); }
      .customer-chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
      .customer-chip { display: inline-flex; align-items: center; padding: 4px 12px; border-radius: 100px; background: var(--accent-soft); color: var(--accent); font-size: 12px; font-weight: 600; }
      
      .customer-price-table { margin-top: 32px; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
      .customer-price-table table { margin: 0; }
      .customer-price-table th { background: #F3F4F6; color: #374151; font-weight: 700; padding: 12px 16px; text-transform: none; border-bottom: 2px solid var(--line); }
      .customer-price-table td { padding: 16px; border-bottom: 1px solid var(--line); }
      .customer-price-table tbody tr:last-child td { border-bottom: 0; }
      .customer-price-table .grand-row td { font-weight: 800; background: var(--accent-soft); color: var(--accent); font-size: 16px; border-top: 2px solid var(--line); }
      .customer-price-table .manual-row td { color: var(--accent); }
      
      .customer-note-box { margin-top: 32px; padding-top: 24px; border-top: 1px solid var(--line); }
      .customer-note-box strong { display: block; margin-top: 8px; font-size: 15px; color: #374151; }
      .customer-note-box ul { margin: 12px 0 0; padding-left: 20px; color: #6B7280; font-size: 14px; line-height: 1.6; }
      
      /* Settings Modal */
      .settings-modal { position: fixed; inset: 0; background: rgba(17, 24, 39, 0.6); backdrop-filter: blur(4px); z-index: 1000; overflow: auto; padding: 32px; display: flex; align-items: flex-start; justify-content: center; }
      .settings-panel { width: 100%; max-width: 1100px; background: #FFFFFF; border-radius: 12px; box-shadow: var(--shadow-lg); padding: 32px; margin-top: 4vh; margin-bottom: 4vh; }
      .settings-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 24px; padding-bottom: 20px; border-bottom: 1px solid var(--line); }
      .settings-header .section-title { font-size: 20px; color: #111827; text-transform: none; font-weight: 700; }
      .settings-header p { margin: 8px 0 0; color: var(--muted); font-size: 14px; text-transform: none;}
      .settings-actions { display: flex; gap: 12px; }
      
      .settings-section { margin-top: 24px; padding-top: 24px; border-top: 1px solid var(--line); }
      .settings-section:first-child { border-top: none; padding-top: 0; }
      .settings-section .section-title { font-size: 16px; color: #111827; text-transform: none; margin-bottom: 16px; }
      .settings-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
      
      .settings-service-grid { display: grid; grid-template-columns: minmax(0, 1.6fr) 140px 140px 100px; gap: 16px; align-items: end; padding: 12px; background: #F9FAFB; border: 1px solid var(--line); border-radius: 6px; margin-bottom: 12px; }
      .settings-service-grid .field label { font-size: 12px; }
      
      .helper { margin-top: 24px; padding: 16px; border-left: 4px solid var(--accent); background: var(--accent-soft); color: #9A3412; font-size: 14px; line-height: 1.6; border-radius: 0 8px 8px 0; }
      .hidden { display: none !important; }
      
      @media (max-width: 1100px) { .hero, .workspace { grid-template-columns: 1fr; } .panel.result { position: relative; top: 0; max-width: 100%;} }
      @media (max-width: 760px) {
        .page { padding: 16px; } .hero { display: block; } .hero-stat { grid-template-columns: 1fr; margin-top: 24px; }
        .form-grid, .weight-grid, .summary-grid, .totals-grid, .service-row, .box-group-row, .customer-sheet-meta, .customer-summary-grid, .settings-grid, .settings-service-grid { grid-template-columns: 1fr; }
        .box-group-row { display: flex; flex-direction: column; align-items: stretch; gap: 12px; } .totals-secondary-row { grid-template-columns: 1fr; } .quote-actions .action-row { grid-template-columns: 1fr; }
      }
      @media print {
        @page { size: A4 portrait; margin: 15mm; }
        body { background: #fff; font-size: 12pt; }
        body.print-customer-sheet .page > section:not(.customer-sheet), 
        body.print-customer-sheet .page > main { display: none !important; }
        body.print-customer-sheet .page > .customer-sheet { display: block !important; margin: 0; padding: 0; box-shadow: none; border: 0; }
        body.print-customer-sheet .settings-modal { display: none !important; }
        .customer-sheet-head { border-bottom: 2px solid #000; padding-bottom: 24px; }
        .customer-price-table th { background: #f0f0f0 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      }"""

content = re.sub(r'<style>.*?</style>', '<style>\n' + new_css + '\n    </style>', content, flags=re.DOTALL)

# HTML Updates
old_hero = re.search(r'<section class="hero">.*?</section>', content, re.DOTALL).group(0)
new_hero = """      <section class="hero">
        <div class="hero-text">
          <div class="eyebrow">ZYD USA WAREHOUSE</div>
          <h1>代发及入仓报价工作台</h1>
          <p>录入包裹的装箱尺寸与业务模式，系统自动换算材积重与计费档位，生成内部财务明细账单，并可一键出具标准正规的商务对客报价单。</p>
        </div>
        <div class="hero-stat">
          <div><span class="meta-label">当前推荐计费档位</span><strong id="heroBracket">-</strong></div>
          <div><span class="meta-label">核心测算最高磅重</span><strong id="heroChargeableLb">0.00 LB</strong></div>
          <div><span class="meta-label">本次合计预估总报价</span><strong id="heroGrandTotal">$0.00</strong></div>
        </div>
      </section>"""
content = content.replace(old_hero, new_hero)

# Totals Update
old_totals = re.search(r'<div class="totals-grid">.*?</div>', content, re.DOTALL).group(0)
new_totals = """          <div class="totals-grid">
            <div class="metric-card"><span class="meta-label">合计测算总报价 (USD)</span><strong id="grandTotalView">$0.00</strong></div>
            <div class="totals-secondary-row">
              <div class="metric-card metric-card-secondary"><span class="meta-label">单件均摊参考成本</span><strong id="unitCostView">$0.00</strong></div>
              <div class="metric-card metric-card-secondary"><span class="meta-label">最高命中结算档位</span><strong id="matchedBracketView">-</strong></div>
            </div>
          </div>"""
content = content.replace(old_totals, new_totals)

# Actions Update
old_actions = re.search(r'<div class="quote-actions">.*?</div>', content, re.DOTALL).group(0)
new_actions = """          <div class="quote-actions">
            <button class="button" id="generateCustomerQuoteBtn" type="button">确认生成《客户报价单》</button>
            <div class="action-row">
              <button class="button-secondary" id="printCustomerQuoteBtn" type="button">直接打印 PDF</button>
              <button class="button-secondary" id="openSettingsBtn" type="button">核心价格参数设置</button>
            </div>
          </div>"""
content = content.replace(old_actions, new_actions)

# Customer Sheet Head Update
old_sheet_head = re.search(r'<div class="customer-sheet-head">.*?<div class="customer-meta-card">', content, re.DOTALL).group(0)
new_sheet_head = """        <div class="customer-sheet-head">
          <div class="customer-brand">
            <div class="logo-slot" id="customerQuoteLogoSlot">
              <img id="customerQuoteLogo" class="hidden" alt="公司 Logo" />
              <span id="customerQuoteLogoPlaceholder">仲易达供应链</span>
            </div>
            <div class="customer-brand-titles">
              <div class="eyebrow">QUOTATION INVOICE</div>
              <h2>美国一件代发报价单</h2>
            </div>
          </div>
          <div class="quote-grand-block">
            <span class="meta-label">合计报价金额 (USD)</span>
            <strong id="customerQuoteGrandTotal">$0.00</strong>
          </div>
        </div>
        <div class="customer-meta-card">"""
content = content.replace(old_sheet_head, new_sheet_head)

# JS Logo logic update
old_js_logo = """const candidates = ["logo.png", "logo.jpg", "logo.jpeg", "logo.svg", "company-logo.png", "company-logo.jpg"];"""
new_js_logo = """const candidates = ["transparent_仲易达供应链LOGO.png", "副标题_透明底.png", "仲易达供应链LOGO.jpg", "logo.png", "logo.jpg", "logo.jpeg", "logo.svg"];"""
content = content.replace(old_js_logo, new_js_logo)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
