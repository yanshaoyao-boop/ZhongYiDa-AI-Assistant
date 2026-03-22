import * as XLSX from 'xlsx-js-style';

export interface FileData {
  id: number | string;
  name: string;
  status: 'idle' | 'loading' | 'loaded';
  data: any[];
  headers: string[];
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

export const processExcelFile = async (file: File): Promise<Partial<FileData>> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: 'array' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const rows: any[][] = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

        if (rows.length === 0) {
          resolve({ status: 'idle', data: [], headers: [] });
          return;
        }

        // Header Detective
        let headerIdx = 0;
        let headers: string[] = [];
        const keywords = ['号', 'ID', 'id', '价', '金', 'amt', 'price', '客', '户', '员'];

        for (let i = 0; i < Math.min(rows.length, 15); i++) {
          const r = rows[i];
          if (r && r.some(c => c && keywords.some(k => String(c).toLowerCase().includes(k)))) {
            headerIdx = i;
            headers = r.map(h => String(h || '').trim());
            break;
          }
        }

        if (headers.length === 0) {
          headerIdx = 0;
          headers = rows[0].map((h, i) => String(h || `Column ${i + 1}`).trim());
        }

        const idKeys = ['编号', '单号', '货号', 'ID', 'code'];
        const amtKeys = ['金', '额', '价', '总', 'amt', 'price', 'amount'];
        const cliKeys = ['客户', '店铺', '姓名', '买家', 'client', 'customer'];
        const spKeys = ['业务员', 'sales', '跟单', 'rep', '负责人'];

        const findCol = (keys: string[]) => headers.find(h => keys.some(k => h.toLowerCase().includes(k.toLowerCase())));

        resolve({
          status: 'loaded',
          name: file.name,
          headers,
          data: rows.slice(headerIdx + 1),
          headerIdx,
          idCol: findCol(idKeys) || headers[0],
          amtCol: findCol(amtKeys) || headers[1],
          clientCol: findCol(cliKeys) || '',
          salespersonCol: findCol(spKeys) || '',
          currentSheet: sheetName,
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

  // Build Sales Map
  salesFile.data.forEach(row => {
    const id = String(row[sIdIdx] || '').trim();
    if (!id) return;
    const amt = parseFloat(String(row[sAmtIdx] || '0').replace(/,/g, '')) || 0;
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

  // Build Agent Map
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

      const amt = parseFloat(String(row[aAmtIdx] || '0').replace(/,/g, '')) || 0;

      if (agentMap.has(id)) {
        const prev = agentMap.get(id)!;
        prev.amount += amt;
        if (!prev.files.includes(index + 1)) prev.files.push(index + 1);
      } else {
        agentMap.set(id, { amount: amt, files: [index + 1] });
      }
    });
  });

  // Compare
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
