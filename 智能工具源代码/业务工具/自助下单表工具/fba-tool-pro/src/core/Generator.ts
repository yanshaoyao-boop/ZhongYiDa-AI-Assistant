import ExcelJS from 'exceljs';
import JSZip from 'jszip';
import type { RowWithImages, ColumnMapping, TemplateConfig } from '../types/OrderData';

export class Generator {
    static async generateZip(
        dataSource: RowWithImages[],
        templateFile: File,
        mapping: Record<string, string>, // Template Col Name -> Data Col Name
        columns: ColumnMapping[],
        config: TemplateConfig,
        warehouseMap: Record<string, any[]> = {},
        dataStartRow: number = 12
    ): Promise<Blob> {
        const zip = new JSZip();
        // Read template buffer once
        const templateBuffer = await templateFile.arrayBuffer();

        // 1. Group Data
        const groups: Record<string, RowWithImages[]> = {};

        dataSource.forEach(row => {
            const rowVal = row[config.groupBy];
            let key = rowVal ? String(rowVal).trim() : 'Unclassified';
            // Sanitize filename
            key = key.replace(/[\\/:*?"<>|]/g, '-');
            if (!groups[key]) groups[key] = [];
            groups[key]!.push(row);
        });

        // 2. Process Each Group
        for (const [groupName, rows] of Object.entries(groups)) {
            const wb = new ExcelJS.Workbook();
            await wb.xlsx.load(templateBuffer);
            const ws = wb.getWorksheet(1);
            if (!ws) continue;

            // --- Fill Static Info ---
            // M8: Warehouse Name
            const cellM8 = ws.getCell('M8');
            cellM8.value = groupName;

            // --- Pre-calculate Linked Formula Values (Double Write) ---
            if (Object.keys(warehouseMap).length > 0) {
                const whData = warehouseMap[groupName.toUpperCase()];

                if (whData) {
                    // Helper to safely double-write
                    const setCell = (cellAddr: string, colIndex: number) => {
                        const cell = ws.getCell(cellAddr);
                        const val = whData[colIndex];

                        if (val !== undefined) {
                            if (cell.formula) {
                                cell.value = { formula: cell.formula, result: val };
                            } else {
                                cell.value = val;
                            }
                        }
                    };

                    // Based on formula: =VLOOKUP(M8, ... , 3, FALSE) -> Col C -> Index 3 in Excel (1-based)
                    setCell('H3', 3);

                    // Try to auto-detect Col Index for M5 (Zip)
                    const cellM5 = ws.getCell('M5');
                    if (cellM5 && cellM5.formula && cellM5.formula.includes('M8')) {
                        const match = cellM5.formula.match(/,\s*(\d+)\s*,/);
                        if (match && match[1]) {
                            setCell('M5', parseInt(match[1]));
                        }
                    }
                }
            }

            // B9: Declaration Type
            const cellB9 = ws.getCell('B9');
            cellB9.value = config.declareType;

            // F3: Total Box Count
            if (config.sumBy) {
                const total = rows.reduce((sum, r) => {
                    const val = parseFloat(r[config.sumBy]);
                    return sum + (isNaN(val) ? 0 : val);
                }, 0);
                const cellF3 = ws.getCell('F3');
                cellF3.value = total;
            }

            // B3: Reference ID (from first row)
            // find a key that looks like Reference ID or FBA Number
            const refKey = mapping['Reference ID'] || mapping['FBA编号'] || Object.values(mapping)[0];
            if (refKey && rows.length > 0) {
                // @ts-ignore
                const refVal = rows[0][refKey];
                if (refVal) ws.getCell('B3').value = refVal;
            }

            // --- Fill Data Rows ---
            for (let i = 0; i < rows.length; i++) {
                const rowData = rows[i];
                if (!rowData) continue;
                const targetRowIdx = dataStartRow + i;
                const row = ws.getRow(targetRowIdx);

                columns.forEach(col => {
                    const sourceKey = mapping[col.name];
                    const dimLengthKey = mapping[col.name + '_L'];
                    const dimWidthKey = mapping[col.name + '_W'];
                    const dimHeightKey = mapping[col.name + '_H'];

                    // A. Text Fill
                    const isDim = col.name.includes('材积') || (col.name.includes('长') && col.name.includes('宽') && col.name.includes('高'));
                    if (isDim && dimLengthKey && dimWidthKey && dimHeightKey) {
                        const l = rowData[dimLengthKey] || '';
                        const w = rowData[dimWidthKey] || '';
                        const h = rowData[dimHeightKey] || '';
                        if (l || w || h) {
                            row.getCell(col.index + 1).value = `${l}*${w}*${h}`;
                        }
                    } else if (sourceKey && rowData[sourceKey] !== undefined) {
                        row.getCell(col.index + 1).value = rowData[sourceKey];
                    }

                    // B. Image Fill
                    // Check if this column is meant for images
                    const isImageCol = col.name.includes('图片') || col.name.includes('Photo') || col.name.includes('Image');

                    if (isImageCol && rowData._images && rowData._images.length > 0) {
                        // Take the first image found for this row
                        const imgObj = rowData._images[0];
                        if (!imgObj) return;

                        const imgId = wb.addImage({
                            buffer: imgObj.buffer,
                            extension: imgObj.extension
                        });

                        // Centering Logic: Relative Offsets
                        // col + 0.2 (20% padding-left)
                        // row + 0.15 (15% padding-top)
                        ws.addImage(imgId, {
                            tl: { col: col.index + 0.2, row: targetRowIdx - 1 + 0.15 },
                            ext: { width: 50, height: 50 },
                            editAs: 'oneCell'
                        });

                        // Adjust Row Height and Alignment
                        row.height = 60;
                        row.getCell(col.index + 1).alignment = { vertical: 'middle', horizontal: 'center' };
                    }
                });

                row.commit();
            }

            // Write this workbook to buffer
            const outBuffer = await wb.xlsx.writeBuffer();
            zip.file(`${groupName}_OrderList.xlsx`, outBuffer);
        }

        return await zip.generateAsync({ type: 'blob' });
    }
}
