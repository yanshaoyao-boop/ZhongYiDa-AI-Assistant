// 诊断脚本：检查 A.xlsx 中的图片位置
import ExcelJS from 'exceljs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function diagnose() {
    const filePath = path.join(__dirname, '..', '模板', 'A.xlsx');
    console.log('正在分析文件:', filePath);

    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile(filePath);

    const ws = workbook.worksheets[0];
    console.log('\n========== 工作表信息 ==========');
    console.log('工作表名称:', ws.name);
    console.log('总行数:', ws.rowCount);
    console.log('总列数:', ws.columnCount);

    console.log('\n========== 第11行表头 ==========');
    const headerRow = ws.getRow(11);
    const headers = {};
    headerRow.eachCell((cell, colNum) => {
        let val = cell.value;
        if (val && typeof val === 'object') {
            if (val.richText) val = val.richText.map(r => r.text).join('');
            else if (val.result !== undefined) val = val.result;
            else if (val.text) val = val.text;
        }
        headers[colNum] = String(val || '').trim();
        if (headers[colNum]) {
            console.log(`  列 ${colNum}: "${headers[colNum]}"`);
        }
    });

    console.log('\n========== 图片信息 ==========');
    const images = ws.getImages();
    console.log('图片总数:', images.length);

    images.forEach((img, idx) => {
        const tl = img.range.tl;
        const br = img.range.br;

        // nativeRow/nativeCol are 0-based
        const rowNum = tl.nativeRow + 1; // Convert to 1-based
        const colNum = tl.nativeCol + 1;

        const dataRowIndex = rowNum - 12; // Data starts at row 12 (header at 11)
        const headerName = headers[colNum] || '(未知列)';

        console.log(`\n图片 ${idx + 1}:`);
        console.log(`  位置: 行 ${rowNum}, 列 ${colNum} (${String.fromCharCode(64 + colNum)})`);
        console.log(`  对应表头: "${headerName}"`);
        console.log(`  数据行索引: ${dataRowIndex} (第 ${dataRowIndex + 1} 条数据)`);
        console.log(`  imageId: ${img.imageId}`);
    });

    console.log('\n========== workbook.model.media ==========');
    if (workbook.model && workbook.model.media) {
        console.log('Media 数量:', workbook.model.media.length);
        workbook.model.media.forEach((m, i) => {
            console.log(`  Media ${i}: type=${m.type}, name=${m.name}, extension=${m.extension}, index=${i}`);
        });
    } else {
        console.log('无 media 数据');
    }
}

diagnose().catch(console.error);
