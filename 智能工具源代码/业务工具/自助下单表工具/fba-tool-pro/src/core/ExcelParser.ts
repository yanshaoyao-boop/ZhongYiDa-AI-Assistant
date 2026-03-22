import ExcelJS from 'exceljs';
import type { RowWithImages, ImageAsset } from '../types/OrderData';

export class ExcelParser {
    static async fileToBuffer(file: File): Promise<ArrayBuffer> {
        return await file.arrayBuffer();
    }

    /**
     * Parses a data source Excel file, extracting rows and associated images.
     * Uses fuzzy row matching for images.
     */
    static async parseDataSource(file: File): Promise<{ headers: string[], data: RowWithImages[] }> {
        const buffer = await this.fileToBuffer(file);
        const wb = new ExcelJS.Workbook();
        await wb.xlsx.load(buffer);
        const ws = wb.getWorksheet(1); // Default to first sheet

        if (!ws) throw new Error('Excel file is empty or invalid.');

        // 1. Image Extraction Logic
        const imgs = ws.getImages();
        const rowToImgMap: Record<number, ImageAsset[]> = {};

        imgs.forEach(img => {
            const range = img.range;
            const tl = range.tl;
            const br = range.br;

            // Fuzzy Logic: Center point of the image determines the row
            const startRow = Math.floor(tl.row) + 1;
            const centerRow = Math.floor((tl.row + br.row) / 2) + 1;

            // Avoid headers (assuming header is row 1)
            let targetRow = startRow;
            if (targetRow < 2) targetRow = centerRow;

            if (!rowToImgMap[targetRow]) rowToImgMap[targetRow] = [];

            // The imageId from getImages() is a string that represents the internal ID
            // but getImage() expects a number or string depending on version. 
            // We use type assertion to handle ExcelJS's internal ID.
            const imgAsset = wb.getImage(img.imageId as any);
            if (imgAsset) {
                rowToImgMap[targetRow]!.push({
                    buffer: imgAsset.buffer as ArrayBuffer,
                    extension: imgAsset.extension as 'jpeg' | 'png' | 'gif'
                });
            }
        });

        // 2. Data Row Extraction
        const allData: RowWithImages[] = [];
        const headersSet = new Set<string>();

        const headerRow = ws.getRow(1);
        const fileColMap: string[] = []; // colIndex -> headerName

        headerRow.eachCell((cell, colNum) => {
            const val = cell.text ? cell.text.trim() : '';
            if (val) {
                fileColMap[colNum] = val;
                headersSet.add(val);
            }
        });

        ws.eachRow((row, rowNum) => {
            if (rowNum <= 1) return; // Skip header

            const rowObj: RowWithImages = { _source: file.name };

            // Fill text data
            fileColMap.forEach((key, colIdx) => {
                const cell = row.getCell(colIdx);
                // Handle formulas or raw values
                // @ts-ignore: value structure might vary
                const val = (cell.value && cell.value.result !== undefined) ? cell.value.result : cell.value;
                rowObj[key] = val;
            });

            // Attach images
            if (rowToImgMap[rowNum]) {
                rowObj._images = rowToImgMap[rowNum];
            }

            // Only add if row has data or images
            if (Object.keys(rowObj).length > 1 || rowObj._images) {
                allData.push(rowObj);
            }
        });

        return {
            headers: Array.from(headersSet),
            data: allData
        };
    }

    static async parseTemplateHeaders(file: File, headerRowIndex: number = 11): Promise<{ index: number, name: string }[]> {
        const buffer = await this.fileToBuffer(file);
        const wb = new ExcelJS.Workbook();
        await wb.xlsx.load(buffer);
        const ws = wb.getWorksheet(1);

        if (!ws) throw new Error('Template sheet not found');

        const headerRow = ws.getRow(headerRowIndex);
        const columns: { index: number, name: string }[] = [];

        headerRow.eachCell((cell, colNumber) => {
            const val = cell.text ? cell.text.trim() : '';
            if (val) {
                columns.push({
                    index: colNumber - 1, // 0-based for easy array mapping
                    name: val
                });
            }
        });

        return columns;
    }
    /**
     * Tries to find and parse the hidden "Amazon Warehouse Address" sheet.
     * Returns a map of WarehouseCode -> RowData (Array)
     */
    static async parseHiddenWarehouseSheet(file: File): Promise<Record<string, any[]>> {
        const buffer = await this.fileToBuffer(file);
        const wb = new ExcelJS.Workbook();
        await wb.xlsx.load(buffer);

        // Try to find the sheet by likely names
        let sheetName = '';
        wb.eachSheet((s) => {
            if (s.name.includes('地址') || s.name.includes('Address') || s.name.includes('仓库')) {
                sheetName = s.name;
            }
        });

        if (!sheetName) return {};

        const ws = wb.getWorksheet(sheetName);
        if (!ws) return {};

        const map: Record<string, any[]> = {};

        // Assume Row 1 is header, data starts from Row 2
        // Assume Column A (1) is the Warehouse Code (Key)
        ws.eachRow((row, rowNum) => {
            if (rowNum < 2) return;
            // index 1 is Col A
            const keyCell = row.getCell(1);
            const key = keyCell.text ? keyCell.text.trim().toUpperCase() : '';

            if (key) {
                // Store the whole row values (1-based index)
                const values: any[] = [];
                row.eachCell({ includeEmpty: true }, (cell, colNum) => {
                    // Extract value, prioritizing calculated result if exists
                    // @ts-ignore
                    const v = (cell.value && cell.value.result !== undefined) ? cell.value.result : cell.value;
                    values[colNum] = v;
                });
                map[key] = values;
            }
        });

        console.log('Parsed Warehouse Map with', Object.keys(map).length, 'entries from sheet:', sheetName);
        return map;
    }
}
