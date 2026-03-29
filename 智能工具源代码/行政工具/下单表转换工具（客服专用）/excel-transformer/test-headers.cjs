const ExcelJS = require('exceljs');
const fs = require('fs');

async function test() {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile('D:\\Antigravity-work\\Projects\\Dev-Forge\\下单表转换工具（客服专用）\\模板\\C.xlsx');
    const ws = workbook.worksheets[0];
    const headerRow = ws.getRow(17);
    const headers = [];
    headerRow.eachCell((cell, colNum) => {
        let val = cell.value;
        if (typeof val === 'string') val = val.trim();
        else if (val && typeof val === 'object' && val.richText) val = val.richText.map(rt => rt.text).join('').trim();
        if (val) headers.push(val);
    });
    console.log("C Row 17:", headers);

    // Check row 16 just in case
    const headerRow16 = ws.getRow(16);
    const headers16 = [];
    headerRow16.eachCell((cell, colNum) => {
        let val = cell.value;
        if (typeof val === 'string') val = val.trim();
        else if (val && typeof val === 'object' && val.richText) val = val.richText.map(rt => rt.text).join('').trim();
        if (val) headers16.push(val);
    });
    console.log("C Row 16:", headers16);
}
test().catch(console.error);
