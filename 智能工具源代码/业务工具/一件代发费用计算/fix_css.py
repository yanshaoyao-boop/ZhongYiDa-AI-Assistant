import re

file_path = r'd:\Antigravity-work\Projects\Dev-Forge\一件代发费用计算\美国一件代发报价计算器.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the COMPLETE NEW CLEAN CSS
full_new_css = """      :root {
        --bg: #F8F9FA;
        --paper: #FFFFFF;
        --ink: #1A1B1E;
        --muted: #6B7280;
        --line: #E5E7EB;
        --accent: #D05000;
        --accent-hover: #A03D00;
        --accent-soft: rgba(208, 80, 0, 0.1);
        --shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        --radius: 12px;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: 'Inter', system-ui, sans-serif;
        color: var(--ink);
        background: var(--bg);
        -webkit-font-smoothing: antialiased;
      }
      .page { max-width: 1480px; margin: 0 auto; padding: 32px; }
      .hero { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 32px; align-items: end; margin-bottom: 32px; }
      .hero-text { max-width: 720px; }
      .eyebrow, .meta-label, .field label, .section-title, th { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }
      .eyebrow { color: var(--accent); margin-bottom: 8px; display: inline-block; }
      h1 { margin: 0; font-size: 42px; font-weight: 800; line-height: 1.1; letter-spacing: -0.02em; color: #111827; }
      .hero-text p { margin: 12px 0 0; color: var(--muted); line-height: 1.6; font-size: 16px; }
      
      .hero-stat { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; padding: 24px 32px; background: #FFFFFF; border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow); }
      .hero-stat > div { display: flex; flex-direction: column; gap: 8px; }
      .hero-stat strong { font-size: 28px; font-weight: 700; color: #111827; }
      #heroGrandTotal { color: var(--accent); }

      .workspace { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(420px, 0.45fr); gap: 32px; align-items: start; }
      
      .panel { background: var(--paper); border-radius: var(--radius); border: 1px solid var(--line); box-shadow: var(--shadow); }
      .panel.form { padding: 32px; }
      .panel.result { padding: 32px; position: sticky; top: 32px; background: #FFF; border: 1px solid var(--line); box-shadow: var(--shadow); }
      
      .section-header { margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--line); }
      .section-header .section-title { font-size: 15px; color: #111827; }
      .section-header p { margin: 8px 0 0; color: var(--muted); font-size: 14px; line-height: 1.5; }
      
      .quote-meta-block { margin-top: 32px; padding: 24px; background: #F9FAFB; border-radius: 8px; border: 1px dashed #D1D5DB; }
      
      .form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; padding-top: 16px; }
      .field { display: grid; gap: 8px; }
      .field input, .field select, .field textarea { 
        width: 100%; border: 1px solid var(--line); border-radius: 8px; background: #FFFFFF; 
        padding: 10px 14px; font-family: inherit; font-size: 15px; transition: all 0.2s;
      }
      .field input:focus, .field select:focus, .field textarea:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
      
      .box-group-row {
        display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)) auto;
        gap: 12px; align-items: end; padding: 16px; margin-bottom: 12px;
        background: #FFFFFF; border: 1px solid var(--line); border-radius: 8px;
      }
      .service-row { display: grid; grid-template-columns: minmax(0, 1.8fr) 120px auto auto; gap: 16px; align-items: end; margin-top: 16px; }
      
      .button, .button-secondary { 
        display: inline-flex; align-items: center; justify-content: center;
        border: 1px solid transparent; border-radius: 6px; padding: 10px 18px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; 
      }
      .button { background: var(--accent); color: #fff; }
      .button:hover { background: var(--accent-hover); }
      .button-secondary { background: #FFFFFF; color: #374151; border-color: #D1D5DB; }
      .button-secondary:hover { background: #F9FAFB; }
      .button-secondary.remove-box-group, .button-secondary.remove-service { color: #EF4444; border: none; background: transparent; }
      
      .metric-card { background: #F9FAFB; border: 1px solid var(--line); border-radius: 8px; padding: 16px; }
      .metric-card strong { display: block; margin-top: 8px; font-size: 20px; font-weight: 700; color: #111827; }
      
      .weight-grid, .summary-grid, .totals-grid { display: grid; gap: 16px; margin-top: 20px; }
      .weight-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
      .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .totals-grid .metric-card { background: var(--accent-soft); border: none; }
      .totals-grid .metric-card strong { font-size: 36px; color: var(--accent); }
      .totals-secondary-row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 12px; }

      .table-wrap { margin-top: 24px; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
      table { width: 100%; border-collapse: collapse; text-align: left; }
      th, td { padding: 14px 16px; border-bottom: 1px solid var(--line); }
      th { background: #F9FAFB; font-size: 12px; color: #6B7280; }
      
      .quote-actions { display: flex; flex-direction: column; gap: 12px; margin-top: 32px; }
      .quote-actions .action-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
      
      .customer-sheet {
        margin-top: 48px; padding: 48px; background: #FFFFFF; color: #111827;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: 1px solid var(--line); border-radius: var(--radius);
      }
      .customer-sheet-head { display: flex; justify-content: space-between; padding-bottom: 32px; border-bottom: 2px solid #111827; }
      .customer-brand { display: flex; gap: 24px; align-items: center; }
      .logo-slot img { height: 64px; max-width: 260px; object-fit: contain; }
      #customerQuoteGrandTotal { font-size: 36px; font-weight: 800; color: var(--accent); }
      
      .customer-price-table { margin-top: 32px; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
      .customer-price-table th { background: #F3F4F6; }
      .customer-price-table .grand-row td { font-weight: 800; background: var(--accent-soft); color: var(--accent); border-top: 2px solid var(--line); }
      
      .hidden { display: none !important; }
      
      @media print {
        @page { size: A4 portrait; margin: 15mm; }
        body { background: #fff !important; }
        
        /* THE FIX: In print mode, hide everything inside .page except the quotation sheet */
        body.print-customer-sheet .page > *:not(.customer-sheet) {
            display: none !important;
        }
        
        body.print-customer-sheet .page { padding: 0 !important; margin: 0 !important; max-width: none !important; }
        
        body.print-customer-sheet .customer-sheet {
            display: block !important;
            margin: 0 !important;
            padding: 0 !important;
            box-shadow: none !important;
            border: none !important;
            width: 100% !important;
        }
        
        /* Ensure logos and colors show correctly in PDF */
        .customer-price-table th { background: #f3f4f6 !important; -webkit-print-color-adjust: exact; }
        #customerQuoteGrandTotal { color: #D05000 !important; -webkit-print-color-adjust: exact; }
      }
"""

content = re.sub(r'<style>.*?</style>', '<style>\n' + full_new_css + '\n    </style>', content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
