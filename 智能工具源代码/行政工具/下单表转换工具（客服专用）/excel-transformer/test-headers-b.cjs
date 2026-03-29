const ExcelJS = require('exceljs');
const fs = require('fs');

async function test() {
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.readFile('D:\\Antigravity-work\\Projects\\Dev-Forge\\下单表转换工具（客服专用）\\模板\\B.xlsx');
    const ws = workbook.worksheets[0];
    const headerRow = ws.getRow(16);
    const headers = [];
    headerRow.eachCell((cell, colNum) => {
        let val = cell.value;
        if (typeof val === 'string') val = val.trim();
        else if (val && typeof val === 'object' && val.richText) val = val.richText.map(rt => rt.text).join('').trim();
        if (val) headers.push(val);
    });
    console.log("B Row 16:", headers);
}
test().catch(console.error);
