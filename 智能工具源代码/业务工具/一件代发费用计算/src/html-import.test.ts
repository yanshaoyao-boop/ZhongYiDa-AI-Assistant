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

  it('uses single-piece actual weight in the box-group template instead of carton weight', () => {
    const html = readFileSync(htmlPath, 'utf-8');

    expect(html).toContain('class="group-piece-weight-kg"');
    expect(html).toContain('单件实重 (kg)');
    expect(html).not.toContain('class="group-weight-kg"');
    expect(html).not.toContain('单箱重量 (kg)');
  });

  it('suppresses spinner controls for number inputs in the standalone html form', () => {
    const html = readFileSync(htmlPath, 'utf-8');

    expect(html).toContain('input[type="number"]::-webkit-outer-spin-button');
    expect(html).toContain('input[type="number"]::-webkit-inner-spin-button');
    expect(html).toContain('-webkit-appearance: none;');
    expect(html).toContain('input[type="number"] {');
    expect(html).toContain('appearance: textfield;');
  });

  it('calculates single-piece chargeable weight from piece actual weight and piece dimensions', () => {
    const html = readFileSync(htmlPath, 'utf-8');

    expect(html).toContain('const volumetricPieceWeightKg = (group.lengthCm * group.widthCm * group.heightCm) / 6000;');
    expect(html).toContain('const chargeablePieceWeightKg = Math.max(group.actualWeightKg, volumetricPieceWeightKg);');
    expect(html).not.toContain('const volumetricBoxWeightKg = (group.lengthCm * group.widthCm * group.heightCm) / 6000;');
    expect(html).not.toContain('group.piecesPerBox > 0 ? chargeableBoxWeightKg / group.piecesPerBox : 0;');
  });

  it('includes contact phone input and a dedicated printed contact line', () => {
    const html = readFileSync(htmlPath, 'utf-8');

    expect(html).toContain('id="contactPhone"');
    expect(html).toContain('id="customerQuoteContactLine"');
    expect(html).toContain('contactPhone: document.getElementById("contactPhone")');
    expect(html).toContain('elements.customerQuoteContactLine.textContent');
  });
});
