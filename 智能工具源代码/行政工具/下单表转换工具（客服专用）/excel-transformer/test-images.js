// 测试新的图片提取逻辑
import JSZip from 'jszip';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import ExcelJS from 'exceljs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const extractCellImages = async (buffer) => {
    const imageMap = new Map();

    try {
        const zip = await JSZip.loadAsync(buffer);

        const cellImagesFile = zip.file('xl/cellimages.xml');
        const cellImagesRelsFile = zip.file('xl/_rels/cellimages.xml.rels');

        if (!cellImagesFile || !cellImagesRelsFile) {
            console.log('No cell images found in this file');
            return imageMap;
        }

        const relsContent = await cellImagesRelsFile.async('string');
        const rIdToPath = {};
        const relsMatches = relsContent.matchAll(/Id="(rId\d+)"[^>]*Target="([^"]+)"/g);
        for (const match of relsMatches) {
            rIdToPath[match[1]] = match[2];
        }
        console.log('rIdToPath:', rIdToPath);

        const cellImagesContent = await cellImagesFile.async('string');
        const picMatches = cellImagesContent.matchAll(/<xdr:cNvPr[^>]*name="([^"]+)"[^>]*>.*?<a:blip[^>]*r:embed="([^"]+)"/gs);

        for (const match of picMatches) {
            const imageId = match[1];
            const rId = match[2];
            const relativePath = rIdToPath[rId];

            console.log(`Processing: imageId=${imageId}, rId=${rId}, path=${relativePath}`);

            if (relativePath) {
                const fullPath = 'xl/' + relativePath;
                const imageFile = zip.file(fullPath);

                if (imageFile) {
                    const imageBuffer = await imageFile.async('arraybuffer');
                    const extension = relativePath.split('.').pop() || 'png';

                    imageMap.set(imageId, {
                        imageId,
                        buffer: imageBuffer,
                        extension
                    });
                    console.log(`✓ Found cell image: ${imageId} -> ${fullPath} (${imageBuffer.byteLength} bytes)`);
                }
            }
        }
    } catch (e) {
        console.warn('Error extracting cell images:', e);
    }

    return imageMap;
};


async function test() {
    const filePath = path.join(__dirname, '..', '模板', 'A.xlsx');
    console.log('Testing file:', filePath);

    const buffer = fs.readFileSync(filePath);

    // 1. Test extractCellImages
    console.log('\n=== Testing extractCellImages ===');
    const cellImageMap = await extractCellImages(buffer);
    console.log('Cell image map size:', cellImageMap.size);

    // 2. Test parsing with ExcelJS
    console.log('\n=== Testing ExcelJS parsing ===');
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.load(buffer);
    const ws = workbook.worksheets[0];

    // Read header row 11
    const headerRow = ws.getRow(11);
    const headers = [];
    headerRow.eachCell((cell, colNum) => {
        let val = cell.value;
        if (val && typeof val === 'object') {
            if (val.richText) val = val.richText.map(r => r.text).join('');
            else if (val.result !== undefined) val = val.result;
            else if (val.text) val = val.text;
        }
        headers[colNum] = String(val || '').trim();
    });
    console.log('Headers:', headers.filter(h => h));

    // Check data rows for DISPIMG formulas
    console.log('\n=== Checking for DISPIMG formulas ===');
    ws.eachRow((row, rowNum) => {
        if (rowNum < 12) return;

        row.eachCell((cell, colNum) => {
            const cellVal = cell.value;
            if (cellVal && typeof cellVal === 'object' && 'formula' in cellVal) {
                const formula = cellVal.formula;
                if (formula.includes('DISPIMG')) {
                    const match = formula.match(/DISPIMG\s*\(\s*"([^"]+)"/i);
                    if (match) {
                        const imageId = match[1];
                        const header = headers[colNum] || `Col${colNum}`;
                        console.log(`Row ${rowNum}, ${header}: Found DISPIMG formula with ID: ${imageId}`);

                        // Check if we have this image
                        if (cellImageMap.has(imageId)) {
                            console.log(`  ✓ Image data available!`);
                        } else {
                            console.log(`  ✗ Image data NOT found`);
                        }
                    }
                }
            }
        });
    });
}

test().catch(console.error);
