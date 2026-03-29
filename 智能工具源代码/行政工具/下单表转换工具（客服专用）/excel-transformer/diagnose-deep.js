// 深度诊断：直接解压 xlsx 查看图片嵌入方式
import JSZip from 'jszip';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function diagnoseDeep() {
    const filePath = path.join(__dirname, '..', '模板', 'A.xlsx');
    console.log('正在深度分析文件:', filePath);

    const fileBuffer = fs.readFileSync(filePath);
    const zip = await JSZip.loadAsync(fileBuffer);

    console.log('\n========== XLSX 内部文件结构 ==========');
    const files = Object.keys(zip.files).sort();
    files.forEach(f => {
        if (!f.includes('node_modules')) {
            console.log(' ', f);
        }
    });

    // 检查 drawings
    console.log('\n========== xl/drawings/ 内容 ==========');
    for (const filename of files) {
        if (filename.startsWith('xl/drawings/') && filename.endsWith('.xml')) {
            console.log(`\n--- ${filename} ---`);
            const content = await zip.file(filename).async('string');
            // 只打印前2000字符
            console.log(content.substring(0, 2000));
            if (content.length > 2000) console.log('... (truncated)');
        }
    }

    // 检查 cellimages (Excel 365 新特性)
    console.log('\n========== xl/cellimages.xml (如果存在) ==========');
    const cellImagesFile = zip.file('xl/cellimages.xml');
    if (cellImagesFile) {
        const content = await cellImagesFile.async('string');
        console.log(content.substring(0, 3000));
    } else {
        console.log('不存在 cellimages.xml');
    }

    // 检查 relationships
    console.log('\n========== xl/_rels/workbook.xml.rels ==========');
    const relsFile = zip.file('xl/_rels/workbook.xml.rels');
    if (relsFile) {
        const content = await relsFile.async('string');
        console.log(content);
    }

    // 检查 worksheets rels
    console.log('\n========== xl/worksheets/_rels/ ==========');
    for (const filename of files) {
        if (filename.startsWith('xl/worksheets/_rels/') && filename.endsWith('.rels')) {
            console.log(`\n--- ${filename} ---`);
            const content = await zip.file(filename).async('string');
            console.log(content);
        }
    }

    // 检查 media 文件夹
    console.log('\n========== xl/media/ 图片文件 ==========');
    for (const filename of files) {
        if (filename.startsWith('xl/media/')) {
            const file = zip.file(filename);
            const size = (await file.async('arraybuffer')).byteLength;
            console.log(`  ${filename} - ${(size / 1024).toFixed(2)} KB`);
        }
    }
}

diagnoseDeep().catch(console.error);
