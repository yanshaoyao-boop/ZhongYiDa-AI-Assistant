// 诊断数据映射问题
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import ExcelJS from 'exceljs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 从 ExcelJS 单元格值中提取可读文本
const extractCellText = (cellValue) => {
    if (cellValue === null || cellValue === undefined) return '';
    if (typeof cellValue === 'string') return cellValue.trim();
    if (typeof cellValue === 'number') return String(cellValue);
    if (typeof cellValue === 'boolean') return String(cellValue);
    if (cellValue instanceof Date) return cellValue.toISOString();

    if (typeof cellValue === 'object') {
        if ('result' in cellValue && cellValue.result !== undefined) {
            return extractCellText(cellValue.result);
        }
        if ('richText' in cellValue && Array.isArray(cellValue.richText)) {
            return cellValue.richText.map(r => r.text || '').join('').trim();
        }
        if ('text' in cellValue && typeof cellValue.text === 'string') {
            return cellValue.text.trim();
        }
        if ('sharedFormula' in cellValue && 'result' in cellValue) {
            return extractCellText(cellValue.result);
        }
    }
    console.warn('Unknown cell value type:', typeof cellValue, cellValue);
    return '';
};

async function diagnose() {
    const filePath = path.join(__dirname, '..', '模板', 'A.xlsx');
    console.log('Diagnosing:', filePath);

    const workbook = new ExcelJS.Workbook();
    const buffer = fs.readFileSync(filePath);
    await workbook.xlsx.load(buffer);
    const ws = workbook.worksheets[0];

    // 读取表头
    const headerRow = ws.getRow(11);
    const headers = [];
    headerRow.eachCell((cell, colNum) => {
        headers[colNum] = extractCellText(cell.value);
    });

    console.log('\n=== 表头 (第11行) ===');
    headers.forEach((h, i) => {
        if (h) console.log(`列 ${i}: "${h}" (长度=${h.length}, 字符码=${[...h].map(c => c.charCodeAt(0)).join(',')})`);
    });

    // 读取第一行数据
    console.log('\n=== 第一行数据 (第12行) ===');
    const dataRow = ws.getRow(12);
    dataRow.eachCell((cell, colNum) => {
        const header = headers[colNum] || `无表头`;
        const rawValue = cell.value;
        const extractedValue = extractCellText(rawValue);

        console.log(`列 ${colNum} [${header.substring(0, 15)}...]: `);
        console.log(`  原始类型: ${typeof rawValue}`);
        if (typeof rawValue === 'object' && rawValue !== null) {
            console.log(`  原始内容: ${JSON.stringify(rawValue).substring(0, 100)}`);
        }
        console.log(`  提取结果: "${extractedValue}"`);
    });

    // 检查 mapping 配置
    console.log('\n=== 检查映射配置 ===');
    const configPath = path.join(__dirname, 'mapping-config.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));

    for (const [targetField, sourceField] of Object.entries(config.mapping)) {
        if (!sourceField) continue;

        // 查找 sourceField 是否在 headers 中
        const foundIndex = headers.findIndex(h => h === sourceField);
        const fuzzyIndex = headers.findIndex(h => h && h.replace(/\s/g, '') === sourceField.replace(/\s/g, ''));

        console.log(`"${targetField}" -> "${sourceField}"`);
        console.log(`  精确匹配: ${foundIndex > 0 ? '✓ 列' + foundIndex : '✗ 未找到'}`);
        console.log(`  模糊匹配: ${fuzzyIndex > 0 ? '✓ 列' + fuzzyIndex : '✗ 未找到'}`);

        if (foundIndex < 0 && fuzzyIndex > 0) {
            console.log(`  ⚠ 需要模糊匹配！实际表头: "${headers[fuzzyIndex]}"`);
        }
    }
}

diagnose().catch(console.error);
