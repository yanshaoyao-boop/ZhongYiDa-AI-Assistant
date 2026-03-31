const ExcelJS = require('exceljs');
const path = require('path');

(async () => {
    const wb = new ExcelJS.Workbook();
    const filePath = path.join(__dirname, '4.1英欧报价模版-明日之星.xlsx');
    
    try {
        console.log('读取文件:', filePath);
        await wb.xlsx.readFile(filePath);
        
        console.log('工作表数量:', wb.worksheets.length);
        
        wb.worksheets.forEach((ws, idx) => {
            console.log(`工作表${idx}: 名称="${ws.name}", 行数=${ws.rowCount}, 图片数=${ws.getImages().length}`);
        });
        
        const ws = wb.worksheets[0];
        if (ws) {
            console.log('\n--- 前10行内容 ---');
            for (let i = 1; i <= Math.min(10, ws.rowCount); i++) {
                const row = ws.getRow(i);
                const cells = [];
                row.eachCell((c, n) => {
                    if (n <= 20) {
                        const val = c.text || c.value || '';
                        cells.push(`[${n}]${String(val).substring(0, 20)}`);
                    }
                });
                if (cells.length > 0) {
                    console.log(`行${i}:`, cells.join(' | '));
                }
            }
            
            console.log('\n--- 图片信息 ---');
            const images = ws.getImages();
            images.forEach((img, idx) => {
                console.log(`图片${idx}:`, JSON.stringify({
                    range: img.range,
                    imageId: img.imageId
                }, null, 2));
            });
        }
        
    } catch (e) {
        console.log('错误:', e.message);
        console.log(e.stack);
    }
})();
