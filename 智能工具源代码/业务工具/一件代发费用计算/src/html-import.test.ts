import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const htmlPath = resolve(process.cwd(), '美国一件代发报价计算器.html');

describe('standalone html import wiring', () => {
  it('loads the excel import runtime as a classic script for local file usage', () => {
    const html = readFileSync(htmlPath, 'utf-8');

    expect(html).toContain('<script src="vendor/xlsx.full.min.js"></script>');
    expect(html).toContain('<script src="excel-import-runtime.js"></script>');
    expect(html).not.toContain('type="module"');
    expect(html).not.toContain('import { IMPORT_FIELD_DEFINITIONS');
    expect(html).toContain('window.ExcelImportRuntime');
  });

  it('renders a product name field before box count in the box-group template', () => {
    const html = readFileSync(htmlPath, 'utf-8');

    expect(html).toContain('<input class="group-product-name" type="text"');
    expect(html.indexOf('<label>品名</label>')).toBeLessThan(html.indexOf('<label>箱数</label>'));
  });

  it('includes contact phone input and a dedicated printed contact line', () => {
    const html = readFileSync(htmlPath, 'utf-8');

    expect(html).toContain('id="contactPhone"');
    expect(html).toContain('id="customerQuoteContactLine"');
    expect(html).toContain('contactPhone: document.getElementById("contactPhone")');
    expect(html).toContain('elements.customerQuoteContactLine.textContent');
  });
});
