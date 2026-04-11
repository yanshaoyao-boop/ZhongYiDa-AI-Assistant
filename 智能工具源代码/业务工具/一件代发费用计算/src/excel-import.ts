import { utils, type WorkBook } from 'xlsx';

export interface ImportedBoxGroup {
  boxCount: number;
  piecesPerBox: number;
  skuCount: number;
  actualWeightKg: number | null;
  lengthCm: number | null;
  widthCm: number | null;
  heightCm: number | null;
  reference?: string;
  productName?: string;
  declaredPrice?: number | null;
  sourceRowNumber: number;
}

export interface WorksheetMapping {
  reference?: string;
  productName?: string;
  declaredPrice?: string;
  boxCount?: string;
  piecesPerBox?: string;
  totalPieces?: string;
  skuCount?: string;
  actualWeightKg?: string;
  dimensions?: string;
  lengthCm?: string;
  widthCm?: string;
  heightCm?: string;
}

export interface WorksheetDefaults {
  skuCount?: number;
  actualWeightKg?: number;
}

export interface MappedWorksheetRow {
  rowNumber: number;
  boxGroup: ImportedBoxGroup;
  issues: string[];
  rawRow: unknown[];
}

export interface MappedWorksheetResult {
  validRows: MappedWorksheetRow[];
  incompleteRows: MappedWorksheetRow[];
  skippedRows: MappedWorksheetRow[];
}

export interface WorksheetData {
  headers: string[];
  rows: unknown[][];
}

interface MapWorksheetRowsInput {
  headers: string[];
  rows: unknown[][];
  mapping: WorksheetMapping;
  defaults: WorksheetDefaults;
}

const FOOTER_MARKERS = ['出货日期', '审核', '确认', '签字', '签名', '合计', '总计'];
const FIELD_ALIASES: Record<string, string[]> = {
  reference: ['货号', 'sku', '编号', '产品编码', 'item'],
  productName: ['品名', '产品名称', '货物名称', 'name'],
  declaredPrice: ['申报价', '申报价值', 'value', 'price'],
  boxCount: ['总箱数', '箱数', 'ctn', 'carton'],
  piecesPerBox: ['单箱个数', '每箱个数', '每箱件数', '装箱数', 'pcs/ctn'],
  totalPieces: ['总个数', '总件数', '数量', 'total pcs'],
  skuCount: ['每箱sku数', 'sku数', 'sku qty', 'sku count'],
  actualWeightKg: ['单箱重量', '毛重', '净重', '重量', 'kg'],
  dimensions: ['外箱尺寸（厘米）', '外箱尺寸', '箱规', '长宽高', '尺寸', 'cm'],
  lengthCm: ['箱长', '长'],
  widthCm: ['箱宽', '宽'],
  heightCm: ['箱高', '高']
};

function toTrimmedString(value: unknown) {
  if (value === null || value === undefined) return '';
  return String(value).trim();
}

function parseNumericValue(value: unknown) {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null;
  }

  const text = toTrimmedString(value)
    .replace(/,/g, '')
    .replace(/￥|\$/g, '');
  if (!text) return null;

  const numeric = Number(text);
  return Number.isFinite(numeric) ? numeric : null;
}

function getColumnValue(headers: string[], row: unknown[], columnName?: string) {
  if (!columnName) return undefined;
  const index = headers.findIndex((header) => header === columnName);
  return index >= 0 ? row[index] : undefined;
}

function isBlankRow(row: unknown[]) {
  return row.every((cell) => toTrimmedString(cell) === '');
}

function isFooterLikeRow(row: unknown[]) {
  const joined = row.map(toTrimmedString).filter(Boolean).join(' ');
  if (!joined) return false;
  return FOOTER_MARKERS.some((marker) => joined.includes(marker));
}

function getRequiredIssues(boxGroup: ImportedBoxGroup) {
  const issues: string[] = [];

  if (!boxGroup.boxCount || boxGroup.boxCount <= 0) issues.push('缺少箱数');
  if (!boxGroup.piecesPerBox || boxGroup.piecesPerBox <= 0) issues.push('缺少每箱件数');
  if (boxGroup.actualWeightKg === null || boxGroup.actualWeightKg <= 0) issues.push('缺少单箱重量');
  if (boxGroup.lengthCm === null || boxGroup.lengthCm <= 0) issues.push('缺少箱长');
  if (boxGroup.widthCm === null || boxGroup.widthCm <= 0) issues.push('缺少箱宽');
  if (boxGroup.heightCm === null || boxGroup.heightCm <= 0) issues.push('缺少箱高');

  return issues;
}

function normalizeHeader(header: string) {
  return toTrimmedString(header).toLowerCase().replace(/\s+/g, '');
}

export function parseDimensionValue(value: unknown) {
  const text = toTrimmedString(value);
  if (!text) return null;

  const numbers = text.match(/-?\d+(?:\.\d+)?/g);
  if (!numbers || numbers.length < 3) return null;

  const [lengthCm, widthCm, heightCm] = numbers.slice(0, 3).map(Number);
  if (![lengthCm, widthCm, heightCm].every(Number.isFinite)) return null;

  return { lengthCm, widthCm, heightCm };
}

export function suggestMapping(headers: string[]) {
  const normalizedHeaders = headers.map((header) => ({
    raw: header,
    normalized: normalizeHeader(header)
  }));

  return Object.entries(FIELD_ALIASES).reduce<Record<string, string>>((acc, [fieldKey, aliases]) => {
    for (const alias of aliases) {
      const normalizedAlias = alias.replace(/\s+/g, '').toLowerCase();
      const match = normalizedHeaders.find((header) => header.normalized.includes(normalizedAlias));
      if (match) {
        acc[fieldKey] = match.raw;
        break;
      }
    }
    return acc;
  }, {});
}

export function getSheetRows(workbook: WorkBook, sheetName?: string): WorksheetData {
  const targetSheetName = sheetName || workbook.SheetNames[0];
  const sheet = workbook.Sheets[targetSheetName];
  if (!sheet) {
    throw new Error(`未找到工作表：${targetSheetName}`);
  }

  const sheetRows = utils.sheet_to_json(sheet, {
    header: 1,
    raw: false,
    defval: ''
  }) as unknown[][];

  if (!sheetRows.length) {
    return { headers: [], rows: [] };
  }

  const [headerRow, ...rows] = sheetRows;
  const headers = Array.isArray(headerRow) ? headerRow.map((cell) => toTrimmedString(cell)) : [];

  return { headers, rows };
}

export function mapWorksheetRows(input: MapWorksheetRowsInput): MappedWorksheetResult {
  const { headers, rows, mapping, defaults } = input;
  const result: MappedWorksheetResult = {
    validRows: [],
    incompleteRows: [],
    skippedRows: []
  };

  rows.forEach((row, index) => {
    const rowNumber = index + 2;
    const rawReference = toTrimmedString(getColumnValue(headers, row, mapping.reference));
    const rawProductName = toTrimmedString(getColumnValue(headers, row, mapping.productName));
    const rawDeclaredPrice = parseNumericValue(getColumnValue(headers, row, mapping.declaredPrice));
    const boxCount = parseNumericValue(getColumnValue(headers, row, mapping.boxCount)) ?? 0;
    const piecesPerBox =
      parseNumericValue(getColumnValue(headers, row, mapping.piecesPerBox)) ??
      (() => {
        const totalPieces = parseNumericValue(getColumnValue(headers, row, mapping.totalPieces));
        return totalPieces && boxCount > 0 ? totalPieces / boxCount : 0;
      })();
    const skuCount = parseNumericValue(getColumnValue(headers, row, mapping.skuCount)) ?? defaults.skuCount ?? 1;
    const actualWeightKg =
      parseNumericValue(getColumnValue(headers, row, mapping.actualWeightKg)) ?? defaults.actualWeightKg ?? null;

    const parsedDimensions = parseDimensionValue(getColumnValue(headers, row, mapping.dimensions));
    const lengthCm = parseNumericValue(getColumnValue(headers, row, mapping.lengthCm)) ?? parsedDimensions?.lengthCm ?? null;
    const widthCm = parseNumericValue(getColumnValue(headers, row, mapping.widthCm)) ?? parsedDimensions?.widthCm ?? null;
    const heightCm = parseNumericValue(getColumnValue(headers, row, mapping.heightCm)) ?? parsedDimensions?.heightCm ?? null;

    const boxGroup: ImportedBoxGroup = {
      boxCount,
      piecesPerBox,
      skuCount,
      actualWeightKg,
      lengthCm,
      widthCm,
      heightCm,
      reference: rawReference || undefined,
      productName: rawProductName || undefined,
      declaredPrice: rawDeclaredPrice,
      sourceRowNumber: rowNumber
    };

    const mappedRow: MappedWorksheetRow = {
      rowNumber,
      boxGroup,
      issues: [],
      rawRow: row
    };

    if (isBlankRow(row) || (isFooterLikeRow(row) && boxCount <= 0 && piecesPerBox <= 0)) {
      mappedRow.issues = ['已跳过非数据行'];
      result.skippedRows.push(mappedRow);
      return;
    }

    mappedRow.issues = getRequiredIssues(boxGroup);

    if (mappedRow.issues.length > 0) {
      result.incompleteRows.push(mappedRow);
      return;
    }

    result.validRows.push(mappedRow);
  });

  return result;
}
