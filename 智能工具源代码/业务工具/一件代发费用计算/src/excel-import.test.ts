import { describe, expect, it } from 'vitest';
import XLSX from 'xlsx';
import { getSheetRows, mapWorksheetRows, parseDimensionValue, suggestMapping } from './excel-import';

describe('parseDimensionValue', () => {
  it('splits a combined dimension string into length width and height', () => {
    expect(parseDimensionValue('62*47.5*59')).toEqual({
      lengthCm: 62,
      widthCm: 47.5,
      heightCm: 59
    });
  });

  it('accepts dimension strings with multiplication symbols and unit suffixes', () => {
    expect(parseDimensionValue('L62 × W48 × H60 cm')).toEqual({
      lengthCm: 62,
      widthCm: 48,
      heightCm: 60
    });
  });
});

describe('mapWorksheetRows', () => {
  it('maps optional columns, applies defaults, and skips footer rows', () => {
    const result = mapWorksheetRows({
      headers: ['货号', '外箱尺寸（厘米）', '总箱数', '单箱个数'],
      rows: [
        ['TLM25077', '62*62*59', '2', '12'],
        ['出货日期2026年3月10日', '', '', '']
      ],
      mapping: {
        dimensions: '外箱尺寸（厘米）',
        boxCount: '总箱数',
        piecesPerBox: '单箱个数'
      },
      defaults: {
        skuCount: 1,
        actualWeightKg: 8.5
      }
    });

    expect(result.validRows).toHaveLength(1);
    expect(result.skippedRows).toHaveLength(1);
    expect(result.validRows[0].boxGroup).toMatchObject({
      boxCount: 2,
      piecesPerBox: 12,
      skuCount: 1,
      actualWeightKg: 8.5,
      lengthCm: 62,
      widthCm: 62,
      heightCm: 59
    });
  });

  it('marks rows as incomplete when required calculation fields are still missing', () => {
    const result = mapWorksheetRows({
      headers: ['总箱数', '单箱个数', '外箱尺寸（厘米）'],
      rows: [['3', '8', '50*40*30']],
      mapping: {
        dimensions: '外箱尺寸（厘米）',
        boxCount: '总箱数',
        piecesPerBox: '单箱个数'
      },
      defaults: {}
    });

    expect(result.validRows).toHaveLength(0);
    expect(result.incompleteRows).toHaveLength(1);
    expect(result.incompleteRows[0].issues).toContain('缺少单箱重量');
  });
});

describe('getSheetRows', () => {
  it('splits the first row into headers and returns remaining rows as data', () => {
    const workbook = XLSX.utils.book_new();
    const sheet = XLSX.utils.aoa_to_sheet([
      ['货号', '总箱数', '单箱个数'],
      ['TLM25077', 2, 12],
      ['TLM25078', 1, 6]
    ]);

    XLSX.utils.book_append_sheet(workbook, sheet, 'Sheet1');

    expect(getSheetRows(workbook, 'Sheet1')).toEqual({
      headers: ['货号', '总箱数', '单箱个数'],
      rows: [
        ['TLM25077', '2', '12'],
        ['TLM25078', '1', '6']
      ]
    });
  });

  it('returns empty headers and rows for a blank sheet instead of throwing', () => {
    const workbook = XLSX.utils.book_new();
    const sheet = XLSX.utils.aoa_to_sheet([]);

    XLSX.utils.book_append_sheet(workbook, sheet, 'Blank');

    expect(getSheetRows(workbook, 'Blank')).toEqual({
      headers: [],
      rows: []
    });
  });
});

describe('suggestMapping', () => {
  it('prefers outer carton dimensions over inner carton dimensions', () => {
    const mapping = suggestMapping([
      '货号',
      '申报价',
      '品名',
      '体积m³',
      '内箱尺寸',
      '外箱尺寸（厘米）',
      '总箱数',
      '单箱个数',
      '总个数'
    ]);

    expect(mapping.dimensions).toBe('外箱尺寸（厘米）');
  });
});
