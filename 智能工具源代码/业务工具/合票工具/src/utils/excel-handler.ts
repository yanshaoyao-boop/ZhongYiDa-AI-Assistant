import ExcelJS from 'exceljs';
import { saveAs } from 'file-saver';

export interface FileMetadata {
  name: string;
  buffer: ArrayBuffer;
  warehouseCode?: string;
  headerRow?: number;
}

export interface ProcessingLog {
  time: string;
  msg: string;
  type: 'info' | 'success' | 'warn' | 'error';
}

export class ExcelHandler {
  static getSafeCellValue(cell: ExcelJS.Cell): string {
    if (!cell || cell.value === null || cell.value === undefined) return "";
    try {
      const val = cell.value;
      if (typeof val === 'object') {
        if (val && 'richText' in val) {
          return (val as any).richText.map((item: any) => item.text).join('');
        }
        if (val && 'result' in val) {
          return String((val as any).result);
        }
        if (val && 'text' in val) {
          return String((val as any).text);
        }
        if (val && 'hyperlink' in val) {
          return String((val as any).text || (val as any).hyperlink);
        }
      }
      return String(val);
    } catch (e) {
      return "";
    }
  }

  static analyzeSheet(sheet: ExcelJS.Worksheet): { warehouseCode: string; headerRow: number } {
    let warehouseCode = "";
    let headerRow = -1;

    // Search for warehouse code and header in the first 40 rows
    const maxRows = Math.min(40, sheet.rowCount);
    for (let i = 1; i <= maxRows; i++) {
      const row = sheet.getRow(i);
      row.eachCell((cell, colNumber) => {
        const val = this.getSafeCellValue(cell);

        // Warehouse Code Recognition
        if (!warehouseCode) {
          if (val.includes("FBA仓库代码") || val.includes("Consignee")) {
            if (val.split(/[:：]/).length > 1) {
              warehouseCode = val.split(/[:：]/)[1].trim();
            }
            if (!warehouseCode) {
              const nextCell = row.getCell(colNumber + 1);
              const nextVal = this.getSafeCellValue(nextCell);
              if (nextVal && nextVal.length >= 3 && nextVal.length < 15) warehouseCode = nextVal;
            }
          }
          // Regex for common warehouse codes like ABC1, ONT8
          if (!warehouseCode && /^[A-Z]{3,4}\d$/.test(val)) {
            warehouseCode = val;
          }
        }

        // Header Recognition
        const headerKeywords = ["FBA编号", "Reference ID", "中文品名", "SKU", "Item Name"];
        if (headerRow === -1) {
          for (const kw of headerKeywords) {
            if (val.includes(kw)) {
              headerRow = i - 1; // 0-indexed in some contexts but let's stick to what worked
              break;
            }
          }
        }
      });
    }
    return { warehouseCode: warehouseCode || "未分类", headerRow };
  }

  static hasValues(row: ExcelJS.Row): boolean {
    let has = false;
    row.eachCell(cell => {
      if (cell.value !== null && cell.value !== "") has = true;
    });
    return has;
  }

  static async mergeGroup(code: string, files: FileMetadata[], onProgress: (log: ProcessingLog) => void) {
    if (files.length === 0) return;

    onProgress({ time: new Date().toLocaleTimeString(), msg: `开始合并 [${code}]，包含 ${files.length} 个文件...`, type: 'info' });

    try {
      const masterWB = new ExcelJS.Workbook();
      await masterWB.xlsx.load(files[0].buffer);
      const masterSheet = masterWB.worksheets[0];

      // Remove empty rows from the first file (usually starting from row 13)
      const START_CHECK_ROW = 13;
      for (let r = masterSheet.rowCount; r >= START_CHECK_ROW; r--) {
        const row = masterSheet.getRow(r);
        if (!this.hasValues(row)) {
          masterSheet.spliceRows(r, 1);
        }
      }

      let appendRowIdx = masterSheet.rowCount + 1;

      // Append subsequent files
      for (let i = 1; i < files.length; i++) {
        const item = files[i];
        const slaveWB = new ExcelJS.Workbook();
        await slaveWB.xlsx.load(item.buffer);
        const slaveSheet = slaveWB.worksheets[0];

        // Determine where to start copying (usually 2 rows after header, or row 13)
        const startRow = (item.headerRow !== undefined && item.headerRow !== -1) ? (item.headerRow + 2) : 13;
        const slaveMaxRow = slaveSheet.rowCount;

        for (let r = startRow; r <= slaveMaxRow; r++) {
          const srcRow = slaveSheet.getRow(r);
          if (!this.hasValues(srcRow)) continue;

          const destRow = masterSheet.getRow(appendRowIdx);

          srcRow.eachCell({ includeEmpty: true }, (cell, colNumber) => {
            const destCell = destRow.getCell(colNumber);
            destCell.value = cell.value;
            // Deep clone style to avoid references
            if (cell.style) {
              destCell.style = JSON.parse(JSON.stringify(cell.style));
            }
            if (cell.numFmt) destCell.numFmt = cell.numFmt;
          });

          if (srcRow.height) destRow.height = srcRow.height;
          destRow.commit();

          // --- Robust Floating Image Handling ---
          // Pre-map images by their starting row for efficient lookup
          const slaveImages = slaveSheet.getImages();
          const rowImages = slaveImages.filter(img => {
            const rowStart = (img.range.tl as any).nativeRow ?? img.range.tl.row;
            return rowStart === (r - 1);
          });

          for (const image of rowImages) {
            try {
              const imgData = slaveWB.getImage(Number(image.imageId));
              const newImgId = masterWB.addImage({
                buffer: imgData.buffer as any,
                extension: imgData.extension,
              });

              const rowDiff = appendRowIdx - r;
              const range = image.range;
              
              const newRange: any = {
                tl: { 
                  col: (range.tl as any).nativeCol ?? range.tl.col, 
                  row: ((range.tl as any).nativeRow ?? range.tl.row) + rowDiff,
                  colOff: (range.tl as any).colOff,
                  rowOff: (range.tl as any).rowOff
                },
                br: { 
                  col: (range.br as any).nativeCol ?? range.br.col, 
                  row: ((range.br as any).nativeRow ?? range.br.row) + rowDiff,
                  colOff: (range.br as any).colOff,
                  rowOff: (range.br as any).rowOff
                },
                editAs: (range as any).editAs || 'oneCell'
              };
              
              masterSheet.addImage(newImgId, newRange);
            } catch (imgError) {
              console.warn(`Failed to copy image ${image.imageId} from ${item.name}`, imgError);
            }
          }
          // ---------------------------------------

          appendRowIdx++;
        }
      }

      // Update Carton Count
      this.updateCartonCount(masterSheet, files[0], onProgress);

      const buffer = await masterWB.xlsx.writeBuffer();
      const blob = new Blob([buffer as any], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
      saveAs(blob, `[${code}]_合并表_${new Date().getTime()}.xlsx`);

      onProgress({ time: new Date().toLocaleTimeString(), msg: `✅ [${code}] 合并导出成功！`, type: 'success' });

    } catch (e: any) {
      console.error(e);
      onProgress({ time: new Date().toLocaleTimeString(), msg: `❌ [${code}] 合并失败: ${e.message}`, type: 'error' });
    }
  }

  static updateCartonCount(sheet: ExcelJS.Worksheet, firstFile: FileMetadata, onProgress: (log: ProcessingLog) => void) {
    const headerRowIdx = (firstFile.headerRow !== undefined && firstFile.headerRow !== -1) ? (firstFile.headerRow + 1) : 12;
    const headerRow = sheet.getRow(headerRowIdx);

    let cartonColIdx = -1;
    headerRow.eachCell((cell, colNumber) => {
      const val = this.getSafeCellValue(cell).trim();
      if (/^(箱数|件数|Carton|CTN|Box)/i.test(val) && !val.includes("总")) {
        cartonColIdx = colNumber;
      }
    });

    if (cartonColIdx !== -1) {
      let totalCartons = 0;
      for (let r = headerRowIdx + 1; r <= sheet.rowCount; r++) {
        const cell = sheet.getCell(r, cartonColIdx);
        const valStr = this.getSafeCellValue(cell);
        const match = valStr.match(/(\d+(\.\d+)?)/);
        if (match) {
          const val = parseFloat(match[1]);
          if (!isNaN(val)) totalCartons += val;
        }
      }
      onProgress({ time: new Date().toLocaleTimeString(), msg: `统计总箱数: ${totalCartons}`, type: 'info' });

      // Target rows for back-filling (common template positions)
      const targetRows = [3, 1, 2, 4, 5, 6];
      let filled = false;

      for (const r of targetRows) {
        if (r > sheet.rowCount) continue;
        const row = sheet.getRow(r);
        row.eachCell((cell, colNumber) => {
          if (filled) return;
          const val = this.getSafeCellValue(cell);
          if (/(箱数|件数|Qty|Carton)/i.test(val) && (val.includes(":") || val.includes("：") || val.length < 10)) {
            const targetCell = row.getCell(colNumber + 1);
            targetCell.value = totalCartons;
            targetCell.font = { color: { argb: 'FFFF0000' }, bold: true };
            filled = true;
            onProgress({ time: new Date().toLocaleTimeString(), msg: `已回填箱数到第 ${r} 行`, type: 'success' });
          }
        });
        if (filled) break;
      }
    } else {
      onProgress({ time: new Date().toLocaleTimeString(), msg: '未找到箱数列，跳过自动统计', type: 'warn' });
    }
  }
}
