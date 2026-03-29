// 检查 cellimages.xml 的完整内容
import JSZip from 'jszip';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function checkCellImages() {
    const filePath = path.join(__dirname, '..', '模板', 'A.xlsx');
    const fileBuffer = fs.readFileSync(filePath);
    const zip = await JSZip.loadAsync(fileBuffer);

    console.log('========== xl/cellimages.xml ==========');
    const cellImagesFile = zip.file('xl/cellimages.xml');
    if (cellImagesFile) {
        const content = await cellImagesFile.async('string');
        console.log(content);
    }

    console.log('\n========== xl/_rels/cellimages.xml.rels ==========');
    const relsFile = zip.file('xl/_rels/cellimages.xml.rels');
    if (relsFile) {
        const content = await relsFile.async('string');
        console.log(content);
    }

    // 检查 sheet1.xml 看看图片是如何引用的
    console.log('\n========== 在 sheet1.xml 中搜索图片引用 ==========');
    const sheetFile = zip.file('xl/worksheets/sheet1.xml');
    if (sheetFile) {
        const content = await sheetFile.async('string');
        // 搜索包含 image 或 picture 或 cellImage 的部分
        const matches = content.match(/<c[^>]*>.*?(IMAGE|xdr|cellImage|vm:).*?<\/c>/gi);
        if (matches) {
            matches.forEach(m => console.log(m));
        }

        // 搜索 O 列 (产品图片) 的单元格
        const colO = content.match(/<c r="O\d+"[^>]*>.*?<\/c>/gi);
        if (colO) {
            console.log('\n--- O列单元格 (产品图片) ---');
            colO.forEach(c => console.log(c));
        }
    }
}

checkCellImages().catch(console.error);
