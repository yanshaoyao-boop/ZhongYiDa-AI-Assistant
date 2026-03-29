// 诊断 B 表结构
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import ExcelJS from 'exceljs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function diagnoseB() {
    const filePath = path.join(__dirname, '..', '模板', 'B.xlsx');
    console.log('Diagnosing B template:', filePath);

    const workbook = new ExcelJS.Workbook();
    const buffer = fs.readFileSync(filePath);
    await workbook.xlsx.load(buffer);
    const ws = workbook.worksheets[0];

    console.log('工作表名称:', ws.name);
    console.log('总行数:', ws.rowCount);

    // B表表头在第16行
    console.log('\n=== B表表头 (第16行) ===');
    const headerRow = ws.getRow(16);
    const headers = {};

    headerRow.eachCell((cell, colNum) => {
        let val = cell.value;
        if (val && typeof val === 'object') {
            if (val.richText) val = val.richText.map(r => r.text).join('');
            else if (val.result !== undefined) val = val.result;
            else if (val.text) val = val.text;
        }
        const headerText = String(val || '').trim();
        if (headerText) {
            headers[colNum] = headerText;
            console.log(`列 ${colNum} (${String.fromCharCode(64 + colNum)}): "${headerText}"`);
        }
    });

    // 检查映射配置中的目标字段是否存在
    console.log('\n=== 检查目标字段是否存在于B表 ===');
    const configPath = path.join(__dirname, 'mapping-config.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));

    const headerValues = Object.values(headers);

    for (const targetField of Object.keys(config.mapping)) {
        const found = headerValues.find(h => h === targetField);
        const fuzzyFound = headerValues.find(h => h && h.replace(/\s/g, '') === targetField.replace(/\s/g, ''));

        console.log(`"${targetField}":`);
        if (found) {
            console.log(`  ✓ 精确匹配`);
        } else if (fuzzyFound) {
            console.log(`  ⚠ 需要模糊匹配，实际表头: "${fuzzyFound}"`);
        } else {
            console.log(`  ✗ 未找到！`);
        }
    }
}

diagnoseB().catch(console.error);
