import * as XLSX from 'xlsx-js-style';

export interface FileData {
  id: number | string;
  name: string;
  status: 'idle' | 'loading' | 'loaded';
  data: any[];
  headers: string[];
  sheets?: string[];
  idCol: string;
  amtCol: string;
  clientCol?: string;
  salespersonCol?: string;
  currentSheet?: string;
  rawFile?: File;
  headerIdx: number;
}

export interface ReconciliationResult {
  isMatch: boolean;
  discrepancies: Discrepancy[];
  totalChecked: number;
  matchCount: number;
  totalSalesAmt: number;
  totalAgentAmt: number;
  totalDiff: number;
}

export interface Discrepancy {
  id: string;
  client: string;
  sumSales: number;
  countSales: number;
  sumAgent: number;
  files: number[];
  diff: number;
}

const normalizeHeaders = (row: any[] = []): string[] => {
  const counts = new Map<string, number>();
  return Array.from({ length: row.length }, (_, idx) => {
    const base = String(row[idx] || `Column ${idx + 1}`).trim();
    const count = counts.get(base) ?? 0;
    counts.set(base, count + 1);
    return count === 0 ? base : `${base} (${count + 1})`;
  });
};

const detectHeaderRowIndex = (rows: any[][]): number => {
  if (!rows.length) return 0;
  const scanLimit = Math.min(rows.length, 25);
  const keywords = [
    '\u5355', '\u53f7', 'id', '\u7f16\u53f7', '\u7f16\u7801', 'fba', 'sku',
    '\u91d1\u989d', '\u5e94\u6536', '\u5e94\u4ed8', '\u4ef7\u683c', 'price', 'amount',
    '\u5ba2\u6237', '\u5e97\u94fa', '\u4e1a\u52a1\u5458', 'sales'
  ];

  let bestScore = Number.NEGATIVE_INFINITY;
  let bestRow = 0;

  for (let i = 0; i < scanLimit; i++) {
    const row = rows[i] || [];
    if (!row.length) continue;

    const nonEmptyValues = row.filter(cell => String(cell ?? '').trim() !== '');
    if (!nonEmptyValues.length) continue;

    const keywordHits = nonEmptyValues.reduce((count, cell) => {
      const text = String(cell).toLowerCase();
      return count + (keywords.some(keyword => text.includes(keyword)) ? 1 : 0);
    }, 0);

    const stringCells = nonEmptyValues.filter(cell => typeof cell === 'string').length;
    let score = keywordHits * 10 + nonEmptyValues.length + stringCells * 0.5;
    if (i >= 2 && i <= 4) score += 6;
    if (i === 0) score -= 2;

    if (score > bestScore) {
      bestScore = score;
      bestRow = i;
    }
  }
  return bestRow;
};

const selectAmountColumn = (headers: string[]): string => {
  const includeStrong = [
    '\u5e94\u6536', '\u5e94\u4ed8', '\u91d1\u989d', '\u603b\u989d', '\u5408\u8ba1',
    'amount', 'amt', 'total', 'fee', 'receivable', 'payable'
  ];
  const includeMedium = ['\u4ef7', 'price', '\u8d39', '\u6b3e', '\u6210\u672c'];
  const exclude = ['\u65f6\u95f4', '\u65e5\u671f', 'date', 'time', '\u4ed3\u5e93', '\u6e20\u9053', '\u5ba2\u6237'];

  let bestHeader = headers[1] || headers[0] || '';
  let bestScore = Number.NEGATIVE_INFINITY;

  for (const header of headers) {
    const text = String(header).toLowerCase();
    let score = 0;
    if (includeStrong.some(k => text.includes(k))) score += 12;
    if (includeMedium.some(k => text.includes(k))) score += 4;
    if (exclude.some(k => text.includes(k))) score -= 12;
    if (score > bestScore) {
      bestScore = score;
      bestHeader = header;
    }
  }
  return bestHeader;
};

const parseAmount = (value: unknown): number => {
  const text = String(value ?? '')
    .replace(/[\s,\u00a0]/g, '')
    .replace(/[￥¥$]/g, '')
    .trim();
  if (!text) return 0;
  const parsed = parseFloat(text);
  return Number.isFinite(parsed) ? parsed : 0;
};

export const processExcelFile = async (file: File, targetSheet?: string): Promise<Partial<FileData>> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = e => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: 'array' });
        const activeSheet = targetSheet && workbook.SheetNames.includes(targetSheet)
          ? targetSheet
          : workbook.SheetNames[0];
        const worksheet = workbook.Sheets[activeSheet];
        const rows: any[][] = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

        if (!rows.length) {
          resolve({
            status: 'idle',
            data: [],
            headers: [],
            sheets: workbook.SheetNames,
            currentSheet: activeSheet
          });
          return;
        }

        const headerIdx = detectHeaderRowIndex(rows);
        const headers = normalizeHeaders(rows[headerIdx] || []);

        const idKeys = ['\u7f16\u53f7', '\u5355\u53f7', '\u8d27\u53f7', '\u7f16\u7801', '\u8f6c\u53f7', 'fba', 'id', 'code'];
        const cliKeys = ['\u5ba2\u6237', '\u5e97\u94fa', '\u4e70\u5bb6', '\u6765\u6e90', 'client', 'customer', 'shop'];
        const spKeys = ['\u4e1a\u52a1\u5458', '\u9500\u552e', '\u8ddf\u5355', 'sales', 'rep', 'owner'];

        const findCol = (keys: string[]) =>
          headers.find(header => keys.some(keyword => header.toLowerCase().includes(keyword)));

        resolve({
          status: 'loaded',
          name: file.name,
          headers,
          sheets: workbook.SheetNames,
          data: rows.slice(headerIdx + 1),
          headerIdx,
          idCol: findCol(idKeys) || headers[0],
          amtCol: selectAmountColumn(headers),
          clientCol: findCol(cliKeys) || '',
          salespersonCol: findCol(spKeys) || '',
          currentSheet: activeSheet,
          rawFile: file
        });
      } catch (err) {
        reject(err);
      }
    };
    reader.onerror = reject;
    reader.readAsArrayBuffer(file);
  });
};

export const runReconciliation = (
  salesFile: FileData,
  agentFiles: FileData[],
  targetSalesperson: string,
  tolerance: number
): ReconciliationResult => {
  const salesMap = new Map<string, { amount: number; count: number; client: string }>();
  const sIdIdx = salesFile.headers.indexOf(salesFile.idCol);
  const sAmtIdx = salesFile.headers.indexOf(salesFile.amtCol);
  const sCliIdx = salesFile.clientCol ? salesFile.headers.indexOf(salesFile.clientCol) : -1;

  salesFile.data.forEach(row => {
    const id = String(row[sIdIdx] || '').trim();
    if (!id) return;
    const amt = parseAmount(row[sAmtIdx]);
    const client = sCliIdx > -1 ? String(row[sCliIdx] || '').trim() : '';

    if (salesMap.has(id)) {
      const prev = salesMap.get(id)!;
      prev.amount += amt;
      prev.count += 1;
      if (client) prev.client = client;
    } else {
      salesMap.set(id, { amount: amt, count: 1, client });
    }
  });

  const agentMap = new Map<string, { amount: number; files: number[] }>();
  agentFiles.forEach((file, index) => {
    if (file.status !== 'loaded') return;
    const aIdIdx = file.headers.indexOf(file.idCol);
    const aAmtIdx = file.headers.indexOf(file.amtCol);
    const aSpIdx = file.salespersonCol ? file.headers.indexOf(file.salespersonCol) : -1;

    file.data.forEach(row => {
      const id = String(row[aIdIdx] || '').trim();
      if (!id) return;

      if (targetSalesperson !== 'ALL' && aSpIdx > -1) {
        if (String(row[aSpIdx] || '').trim() !== targetSalesperson) return;
      }

      const amt = parseAmount(row[aAmtIdx]);

      if (agentMap.has(id)) {
        const prev = agentMap.get(id)!;
        prev.amount += amt;
        if (!prev.files.includes(index + 1)) prev.files.push(index + 1);
      } else {
        agentMap.set(id, { amount: amt, files: [index + 1] });
      }
    });
  });

  const discrepancies: Discrepancy[] = [];
  let totalChecked = 0;
  let matchCount = 0;
  let totalSalesAmt = 0;
  let totalAgentAmt = 0;

  agentMap.forEach((aData, id) => {
    totalChecked++;
    const sData = salesMap.get(id) || { amount: 0, count: 0, client: '' };
    const diff = sData.amount - aData.amount;

    totalAgentAmt += aData.amount;
    totalSalesAmt += sData.amount;

    if (Math.abs(diff) > tolerance) {
      discrepancies.push({
        id,
        client: sData.client,
        sumSales: sData.amount,
        countSales: sData.count,
        sumAgent: aData.amount,
        files: aData.files,
        diff
      });
    } else {
      matchCount++;
    }
  });

  return {
    isMatch: discrepancies.length === 0,
    discrepancies,
    totalChecked,
    matchCount,
    totalSalesAmt,
    totalAgentAmt,
    totalDiff: totalSalesAmt - totalAgentAmt
  };
};
