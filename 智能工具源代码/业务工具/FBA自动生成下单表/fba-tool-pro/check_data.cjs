const ExcelJS = require('exceljs');
const path = require('path');

(async () => {
    const wb = new ExcelJS.Workbook();
    const filePath = path.join(__dirname, '..', '4.1英欧报价模版-明日之星.xlsx');
    
    try {
        console.log('读取客户数据文件:', filePath);
        await wb.xlsx.readFile(filePath);
        
        console.log('工作表数量:', wb.worksheets.length);
        
        // 测试不同的获取方式
        console.log('\n--- 测试 getWorksheet ---');
        console.log('getWorksheet(1):', wb.getWorksheet(1));
        console.log('getWorksheet(0):', wb.getWorksheet(0));
        console.log('getWorksheet("Sheet1"):', wb.getWorksheet("Sheet1"));
        console.log('worksheets[0]:', wb.worksheets[0]);
        
        // 用 worksheets[0] 来读取
        const ws = wb.worksheets[0];
        if (ws) {
            console.log('\n工作表名称:', ws.name);
            console.log('行数:', ws.rowCount);
            
            // 读取表头
            console.log('\n--- 表头（第1行）---');
            const headerRow = ws.getRow(1);
            const headers = [];
            headerRow.eachCell((c, n) => {
                if (n <= 20) {
                    try {
                        const val = c.value;
                        headers.push({ col: n, name: val });
                    } catch (e) {
                        headers.push({ col: n, name: '(error)' });
                    }
                }
            });
            headers.forEach(h => console.log(`  列${h.col}: ${h.name}`));
            
            // 统计数据行
            let dataRows = 0;
            ws.eachRow((row, rowNum) => {
                if (rowNum > 1) dataRows++;
            });
            console.log('\n数据行数:', dataRows);
        }
        
    } catch (e) {
        console.log('错误:', e.message);
        console.log(e.stack);
    }
})();
