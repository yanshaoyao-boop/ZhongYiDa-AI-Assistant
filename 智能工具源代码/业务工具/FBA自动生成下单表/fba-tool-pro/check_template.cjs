const ExcelJS = require('exceljs');
const path = require('path');

(async () => {
    const wb = new ExcelJS.Workbook();
    const filePath = path.join(__dirname, 'MRZX 下单模板.xlsx');
    
    try {
        console.log('读取模板文件:', filePath);
        await wb.xlsx.readFile(filePath);
        
        console.log('工作表数量:', wb.worksheets.length);
        
        // 检查每个工作表
        wb.worksheets.forEach((ws, idx) => {
            console.log(`\n=== 工作表${idx}: "${ws.name}" ===`);
            
            // 只检查前15行
            for (let i = 1; i <= Math.min(15, ws.rowCount); i++) {
                const row = ws.getRow(i);
                const cells = [];
                row.eachCell((c, n) => {
                    if (n <= 20) {
                        try {
                            const val = c.value;
                            if (val !== null && val !== undefined) {
                                const str = typeof val === 'object' ? JSON.stringify(val).substring(0, 20) : String(val).substring(0, 25);
                                cells.push(`[${n}]${str}`);
                            }
                        } catch (e) {
                            cells.push(`[${n}](error)`);
                        }
                    }
                });
                if (cells.length > 0) {
                    console.log(`  行${i}:`, cells.join(' | '));
                }
            }
        });
        
    } catch (e) {
        console.log('错误:', e.message);
        console.log(e.stack);
    }
})();
