<script setup lang="ts">
// @ts-nocheck
import { ref, computed } from 'vue';
import * as XLSX from 'xlsx';
import ExcelJS from 'exceljs';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';

// 类型定义
type Mapping = Record<string, string>;

// Excel 365 单元格内嵌图片信息
interface CellImageInfo {
  imageId: string;       // e.g. "ID_BB48E5F86BB444ACA4373882166E58FB"
  buffer: ArrayBuffer;   // 图片二进制数据
  extension: string;     // e.g. "png"
}

interface SourceFile {
  name: string;
  workbook?: ExcelJS.Workbook; // Keep full workbook for images
  cellImageMap?: Map<string, CellImageInfo>; // Excel 365 cell images
  data: ArrayBuffer; // Keep raw for fallback
  warehouseCode: string;
  // 地址信息 (A表: M7=省份, H7=城市, H6=地址, M5=邮编, H8=电话)
  province: string;    // 省份
  city: string;        // 城市
  address: string;     // 地址
  phone: string;       // 电话
  zipCode: string;     // 邮编
  totalBoxes: string;  // 总箱数 (A表 F3)
  rows: any[]; // Data rows (SheetJS format for easy mapping access, or parsed from ExcelJS)
  images: Record<number, any>; // Map<RowIndex, ImageObject>
}

// 状态变量
const step = ref(1);
const sourceFiles = ref<SourceFile[]>([]); 
const fileTarget = ref<File | null>(null);
const fileTargetBuffer = ref<ArrayBuffer | null>(null); 
const fileNameTarget = ref('');

// 数据源 (以第一个文件为样本作映射参考)
const headersA = ref<string[]>([]);
const headersTarget = ref<string[]>([]);
const targetType = ref<'B' | 'C' | 'Unknown'>('Unknown');

// 模版名称映射
const templateNames: Record<string, string> = {
  'B': '星夜',
  'C': '亿阳'
};
const getTemplateName = () => templateNames[targetType.value] || '未知模版';

// 映射关系 state
const fieldMapping = ref<Mapping>({});

// 拖拽状态
const isDraggingA = ref(false);
const isDraggingTarget = ref(false);

const isProcessing = ref(false);

// --- 辅助方法 ---

// 从 ExcelJS 单元格值中提取可读文本 (处理公式、富文本、超链接等)
const extractCellText = (cellValue: any): string => {
  if (cellValue === null || cellValue === undefined) return '';
  if (typeof cellValue === 'string') return cellValue.replace(/\r?\n/g, ' ').trim();
  if (typeof cellValue === 'number') return String(cellValue);
  if (typeof cellValue === 'boolean') return String(cellValue);
  if (cellValue instanceof Date) return cellValue.toISOString();
  
  // Object types
  if (typeof cellValue === 'object') {
    // Formula: { formula: '=A1', result: 'xxx' }
    if ('result' in cellValue && cellValue.result !== undefined) {
      return extractCellText(cellValue.result); // result can also be complex
    }
    // RichText: { richText: [{ text: 'xxx' }, ...] }
    if ('richText' in cellValue && Array.isArray(cellValue.richText)) {
      return cellValue.richText.map((r: any) => r.text || '').join('').replace(/\r?\n/g, ' ').trim();
    }
    // Hyperlink: { text: 'xxx', hyperlink: 'http://...' }
    if ('text' in cellValue && typeof cellValue.text === 'string') {
      return cellValue.text.replace(/\r?\n/g, ' ').trim();
    }
    // SharedString or other edge cases - try to stringify
    if ('sharedFormula' in cellValue && 'result' in cellValue) {
       return extractCellText(cellValue.result);
    }
  }
  // Last resort: try JSON (for debugging unknown types)
  console.warn('Unknown cell value type:', cellValue);
  return '';
};

// ★ 提取 Excel 365 单元格内嵌图片 (DISPIMG)

const extractCellImages = async (buffer: ArrayBuffer): Promise<Map<string, CellImageInfo>> => {
  const imageMap = new Map<string, CellImageInfo>();
  
  try {
    const zip = await JSZip.loadAsync(buffer);
    
    // 1. 检查是否存在 cellimages.xml
    const cellImagesFile = zip.file('xl/cellimages.xml');
    const cellImagesRelsFile = zip.file('xl/_rels/cellimages.xml.rels');
    
    if (!cellImagesFile || !cellImagesRelsFile) {
      console.log('No cell images found in this file');
      return imageMap;
    }
    
    // 2. 解析 relationships 获取 rId -> 图片路径 的映射
    const relsContent = await cellImagesRelsFile.async('string');
    const rIdToPath: Record<string, string> = {};
    const relsMatches = relsContent.matchAll(/Id="(rId\d+)"[^>]*Target="([^"]+)"/g);
    for (const match of relsMatches) {
      rIdToPath[match[1]] = match[2]; // e.g. rId1 -> media/image1.png
    }
    
    // 3. 解析 cellimages.xml 获取 imageId (如 ID_xxx) -> rId 的映射
    const cellImagesContent = await cellImagesFile.async('string');
    // 查找 <etc:cellImage> 下的 name 属性和 r:embed
    // 格式: <xdr:pic> ... <xdr:nvPicPr><xdr:cNvPr name="ID_xxx"> ... <a:blip r:embed="rId1">
    const picMatches = cellImagesContent.matchAll(/<xdr:cNvPr[^>]*name="([^"]+)"[^>]*>.*?<a:blip[^>]*r:embed="([^"]+)"/gs);
    
    for (const match of picMatches) {
      const imageId = match[1];  // ID_BB48E5F86BB444ACA4373882166E58FB
      const rId = match[2];      // rId1
      const relativePath = rIdToPath[rId]; // media/image1.png
      
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
          console.log(`Found cell image: ${imageId} -> ${fullPath}`);
        }
      }
    }
  } catch (e) {
    console.warn('Error extracting cell images:', e);
  }
  
  return imageMap;
};

// 解析单个 Excel 文件的数据 (优先尝试 ExcelJS 以获取图片)
const parseExcelData = async (buffer: ArrayBuffer, fileName: string): Promise<SourceFile> => {
  let warehouseCode = '';
  let province = '';
  let city = '';
  let address = '';
  let phone = '';
  let zipCode = '';
  let totalBoxes = '';
  let rows: any[] = [];
  let images: Record<number, any> = {};
  let workbook: ExcelJS.Workbook | undefined;
  let cellImageMap: Map<string, CellImageInfo> = new Map();

  // 1. 尝试用 ExcelJS 读取 (仅 .xlsx)
  if (fileName.endsWith('.xlsx')) {
    try {
      // ★ 先提取 Excel 365 单元格内嵌图片
      cellImageMap = await extractCellImages(buffer);
      
      workbook = new ExcelJS.Workbook();
      await workbook.xlsx.load(buffer);
      const ws = workbook.worksheets[0];

      // 读取仓库代码 M8 (Row 8, Col 13)
      // ExcelJS 1-based. Row 8 = 8. Col M = 13.
      warehouseCode = extractCellText(ws.getCell(8, 13).value);
      
      // ★ 读取地址信息 (A表位置)
      // M7 = 省份, H7 = 城市, H6 = 地址, M5 = 邮编, H8 = 电话
      province = extractCellText(ws.getCell('M7').value);
      city = extractCellText(ws.getCell('H7').value);
      address = extractCellText(ws.getCell('H6').value);
      zipCode = extractCellText(ws.getCell('M5').value);
      phone = extractCellText(ws.getCell('H8').value);
      totalBoxes = extractCellText(ws.getCell('F3').value); // 提取总箱数
      console.log(`关键信息提取: 仓库=${warehouseCode}, 省份=${province}, 城市=${city}, 地址=${address}, 邮编=${zipCode}, 电话=${phone}, 总箱数=${totalBoxes}`);

      // 读取表头 (Row 11)
      const headerRow = ws.getRow(11);
      const headers: string[] = [];
      headerRow.eachCell((cell, colNum) => {
        headers[colNum] = extractCellText(cell.value);
      });

      // 读取数据 (Row 12+)
      let dataRowIdx = 0;
      ws.eachRow((row, rowNum) => {
        if (rowNum < 12) return;
        const rowData: any = {};
        
        row.eachCell((cell, colNum) => {
          const header = headers[colNum];
          if (!header) return;
          
          const cellVal = cell.value;
          
          // ★ 检测 DISPIMG 公式
          if (cellVal && typeof cellVal === 'object' && 'formula' in cellVal) {
            const formula = cellVal.formula as string;
            // 匹配 _xlfn.DISPIMG("ID_xxx", 1)
            const dispImgMatch = formula.match(/DISPIMG\s*\(\s*"([^"]+)"/i);
            if (dispImgMatch) {
              const imageId = dispImgMatch[1];
              const cellImage = cellImageMap.get(imageId);
              if (cellImage) {
                // 找到了单元格内嵌图片！存储引用
                if (!images[dataRowIdx]) images[dataRowIdx] = [];
                images[dataRowIdx].push({
                  header: header,
                  imageId: imageId,
                  cellImage: cellImage,  // 包含实际图片数据
                  type: 'cellImage'
                });
                rowData[header] = '[图片]'; // 标记
                return;
              }
            }
          }
          
          rowData[header] = extractCellText(cellVal);
        });
        
        rows.push(rowData);
        dataRowIdx++;
      });

      // 也检查传统浮动图片 (兼容)
      const floatingImages = ws.getImages();
      floatingImages.forEach((img: any) => {
        let effectiveRow = img.range.tl.nativeRow;
        if (img.range.tl.nativeRowOff > 500000 && img.range.br.nativeRow > img.range.tl.nativeRow) {
            effectiveRow = img.range.br.nativeRow;
        }
        if (effectiveRow < 11 && img.range.br.nativeRow >= 11) {
            effectiveRow = 11;
        }

        const dataRowIndex = effectiveRow - 11; 
        if (dataRowIndex >= 0) {
           if (!images[dataRowIndex]) images[dataRowIndex] = [];
           
           let effectiveCol = img.range.tl.nativeCol;
           if (img.range.tl.nativeColOff > 500000 && img.range.br.nativeCol > img.range.tl.nativeCol) {
               effectiveCol = img.range.br.nativeCol;
           }
           
           const colIndex = effectiveCol + 1;
           const header = headers[colIndex];
           if (header) {
             images[dataRowIndex].push({
               header: header,
               imageId: img.imageId,
               type: 'floating'
             });
           }
        }
      });
      
      // Update global headers if needed
      if (headersA.value.length === 0) headersA.value = headers.filter(h => h);

      return {
        name: fileName,
        workbook,
        cellImageMap,  // 新增：传递图片映射
        data: buffer,
        warehouseCode,
        province,      // 新增：省份
        city,          // 新增：城市
        address,       // 新增：地址
        phone,         // 新增：电话
        zipCode,       // 新增：邮编
        totalBoxes,    // 新增：总箱数
        rows,
        images
      };

    } catch (e) {
      console.warn("ExcelJS load failed, falling back to SheetJS", e);
    }
  }

  // Fallback / .xls handling using SheetJS
  const wb = XLSX.read(buffer);
  const ws = wb.Sheets[wb.SheetNames[0]];

  // 1. 读取仓库代码 M8
  const cellM8 = ws['M8'];
  warehouseCode = cellM8 ? extractCellText(cellM8.v) : '';

  // ★ 读取地址信息 (SheetJS fallback)
  province = ws['M7'] ? extractCellText(ws['M7'].v) : '';
  city = ws['H7'] ? extractCellText(ws['H7'].v) : '';
  address = ws['H6'] ? extractCellText(ws['H6'].v) : '';
  zipCode = ws['M5'] ? extractCellText(ws['M5'].v) : '';
  phone = ws['H8'] ? extractCellText(ws['H8'].v) : '';
  totalBoxes = ws['F3'] ? extractCellText(ws['F3'].v) : '';

  // 2. 读取表头 (第11行 -> index 10)
  const jsonData = XLSX.utils.sheet_to_json(ws, { header: 1, range: 10 });
  let headers: string[] = [];

  if (jsonData.length > 0) {
    headers = (jsonData[0] as any[]).map(h => String(h || '')).filter(h => h);
    const rawData = XLSX.utils.sheet_to_json(ws, { range: 10 });
    rows = rawData;
  }
  
  if (headersA.value.length === 0) headersA.value = headers;

  return { name: fileName, data: buffer, warehouseCode, province, city, address, phone, zipCode, totalBoxes, rows, images: {} };
};

// 处理 A 处的文件上传
const handleFilesA = async (files: FileList | null) => {
  if (!files || files.length === 0) return;
  
  const newSourceFiles: SourceFile[] = [];

  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    
    // 如果是 Zip
    if (file.name.endsWith('.zip')) {
      const zip = new JSZip();
      const zipContent = await zip.loadAsync(file);
      for (const [relativePath, zipEntry] of Object.entries(zipContent.files)) {
        if (!zipEntry.dir && (relativePath.endsWith('.xls') || relativePath.endsWith('.xlsx')) && !relativePath.startsWith('__MACOSX')) {
          const content = await zipEntry.async('arraybuffer');
          const parsed = await parseExcelData(content, zipEntry.name.split('/').pop() || zipEntry.name);
          newSourceFiles.push(parsed);
        }
      }
    } 
    // 如果是 Excel
    else if (file.name.endsWith('.xls') || file.name.endsWith('.xlsx')) {
      const buffer = await file.arrayBuffer();
      const parsed = await parseExcelData(buffer, file.name);
      newSourceFiles.push(parsed);
    }
  }

  sourceFiles.value = [...sourceFiles.value, ...newSourceFiles];
};

const removeSourceFile = (index: number) => {
  sourceFiles.value.splice(index, 1);
  if (sourceFiles.value.length === 0) {
    headersA.value = [];
  }
};

// 读取目标文件 B/C
const handleFileTarget = async (file: File) => {
  fileTarget.value = file;
  fileNameTarget.value = file.name;
  fileTargetBuffer.value = await file.arrayBuffer();

  const wb = XLSX.read(fileTargetBuffer.value);
  const ws = wb.Sheets[wb.SheetNames[0]];

  // 判定 B 还是 C
  const row16 = XLSX.utils.sheet_to_json(ws, { header: 1, range: 15, key: 'preview' })[0] as any[];
  
  const name = file.name.toUpperCase();
  if (name.includes('B')) {
    targetType.value = 'B';
  } else if (name.includes('C')) {
    targetType.value = 'C';
  } else {
    if (row16 && row16.filter((c:any) => c).length > 2) {
      targetType.value = 'B';
    } else {
      targetType.value = 'C';
    }
  }

  // 获取 Header
  let headerRowIndex = 15; // Default B (row 16)
  if (targetType.value === 'C') {
    headerRowIndex = 16; // C (row 17)
  }

  const jsonData = XLSX.utils.sheet_to_json(ws, { header: 1, range: headerRowIndex });
  if (jsonData.length > 0) {
    headersTarget.value = (jsonData[0] as any[]).map(h => String(h || '')).filter(h => h);
    
    // 初始化 mapping
    const initialMap: Mapping = {};
    headersTarget.value.forEach(tHeader => {
      // 模糊匹配：忽略空格
      const match = headersA.value.find(hA => hA === tHeader || hA.trim() === tHeader.trim());
      initialMap[tHeader] = match || '';
    });
    fieldMapping.value = initialMap;
  }
};

// 检查是否可以进入下一步
const canNextStep = computed(() => {
  return sourceFiles.value.length > 0 && fileTarget.value;
});

// --- 模版导入/导出 ---
const exportTemplate = () => {
  const config = {
    targetType: targetType.value,
    mapping: fieldMapping.value,
    name: 'ExelTransformerTemplate'
  };
  const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
  saveAs(blob, 'mapping-config.json');
};

const importTemplateInput = ref<HTMLInputElement | null>(null);
const handleImportTemplate = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const config = JSON.parse(e.target?.result as string);
      if (config.mapping) {
        headersTarget.value.forEach(h => {
          if (config.mapping[h]) {
            fieldMapping.value[h] = config.mapping[h];
          }
        });
        alert('模版导入成功！');
      }
    } catch (err) {
      alert('模版文件格式错误');
    }
  };
  reader.readAsText(file);
};

// --- ★ 核心转换逻辑 (使用 ExcelJS) ---

const processConversion = async () => {
  if (!fileTargetBuffer.value) return;
  isProcessing.value = true;

  try {
    // 强制检查模版格式
    if (!fileNameTarget.value.endsWith('.xlsx')) {
      alert('【严重警告】\n\n您正在使用 .xls 格式的模版。\n这会导致所有格式、颜色、公式丢失！\n\n请务必先在 Excel 中将模版“另存为” .xlsx 格式再上传！');
      isProcessing.value = false;
      return;
    }

    const outputZip = new JSZip();

    // 针对每个源文件进行生成
    for (const sourceFile of sourceFiles.value) {
      const workbook = new ExcelJS.Workbook();
      await workbook.xlsx.load(fileTargetBuffer.value);
      const worksheet = workbook.worksheets[0];

      let headerRowIdx = 16;
      let dataStartRowForInsert = 17;
      let warehouseCell = 'B3';

      if (targetType.value === 'C') {
        headerRowIdx = 17;
        dataStartRowForInsert = 18;
        warehouseCell = 'B5';
      }

      // 填写仓库代码
      const cellWh = worksheet.getCell(warehouseCell);
      cellWh.value = sourceFile.warehouseCode;
      
      // ★ 地址和电话填写
      if (targetType.value === 'B') {
        // B表位置: B10=省份, B9=城市, B6=地址, B13=电话, B11=邮编
        worksheet.getCell('B10').value = sourceFile.province || '';
        worksheet.getCell('B9').value = sourceFile.city || '';
        worksheet.getCell('B6').value = sourceFile.address || '';
        worksheet.getCell('B13').value = sourceFile.phone || '';
        worksheet.getCell('B11').value = sourceFile.zipCode || '';
        console.log(`地址信息写入B表: 省份=${sourceFile.province}, 城市=${sourceFile.city}, 地址=${sourceFile.address}, 电话=${sourceFile.phone}, 邮编=${sourceFile.zipCode}`);
      } else if (targetType.value === 'C') {
        // C表位置: B8=地址, B14=电话
        if (sourceFile.address) worksheet.getCell('B8').value = sourceFile.address;
        if (sourceFile.phone) worksheet.getCell('B14').value = sourceFile.phone;
        console.log(`地址信息写入C表: 地址=${sourceFile.address}, 电话=${sourceFile.phone}`);
      }
      
      // ★ 填写总箱数 (B表: B15, C表: B16)
      const totalBoxesCell = targetType.value === 'C' ? 'B16' : 'B15';
      worksheet.getCell(totalBoxesCell).value = sourceFile.totalBoxes || '';
      console.log(`总箱数写入 ${totalBoxesCell}: ${sourceFile.totalBoxes}`);
      
      // ★ 填写客户编码 (原样使用 A 表第一行的 FBA编号)
      // B表: B1, C表: B2
      const firstRowFbaCode = sourceFile.rows.length > 0 ? String(sourceFile.rows[0]['FBA编号'] || '') : '';
      if (firstRowFbaCode) {
        const customerCodeCell = targetType.value === 'C' ? 'B2' : 'B1';
        worksheet.getCell(customerCodeCell).value = firstRowFbaCode;
        console.log(`客户编码写入 ${customerCodeCell}: ${firstRowFbaCode}`);
      }
      
      const rowsToWrite = sourceFile.rows;
      if (rowsToWrite.length === 0) {
        // 如果没数据，直接保存
      } else {
        const headerRow = worksheet.getRow(headerRowIdx);
        const colMap: Record<string, number> = {}; 
        headerRow.eachCell((cell, colNumber) => {
          // ★ 使用 extractCellText 处理复杂单元格值
          const val = extractCellText(cell.value);
          if (val) {
            colMap[val] = colNumber;
            console.log(`B表列映射: "${val}" -> 列${colNumber}`);
          }
        });

        // 获取 "样式模版行" (即 dataStartRowForInsert)
        // 这一行通常是空的，留着格式用
        const templateRow = worksheet.getRow(dataStartRowForInsert);

        // 我们开始写入
        // 如果数据超过1行，我们需要 insert 更多行
        // 注意：ExcelJS 的 insertRow 并不是很好用，我们手动复制样式会更稳
        
        // ★ 货箱编号转换逻辑
        // 累计计数器，跨行累计
        let cumulativeBoxCount = 0;
        
        // 生成货箱编号的函数
        const generateBoxNumber = (fbaCode: string, boxCount: number): string => {
          const startNum = cumulativeBoxCount + 1;
          const endNum = cumulativeBoxCount + boxCount;
          cumulativeBoxCount = endNum; // 更新累计
          
          const startPadded = String(startNum).padStart(6, '0');
          if (boxCount === 1) {
            // 如果箱数为 1，不需要加 "- 结束序号"
            return `${fbaCode}U${startPadded}`;
          } else {
            // 规则：FBA编号 + U + 6位起始序号 + "-" + 结束序号
            return `${fbaCode}U${startPadded}-${endNum}`;
          }
        };
        
        // 我们从 i=0 开始写到 dataStartRowForInsert
        // 当 i > 0 时，我们需要 insertRow(dataStartRowForInsert + i)
        
        for (let i = 0; i < rowsToWrite.length; i++) {
          const rowA = rowsToWrite[i];
          const currentRowIdx = dataStartRowForInsert + i;
          
          let currentRow: ExcelJS.Row;
          
          if (i === 0) {
            currentRow = worksheet.getRow(currentRowIdx);
          } else {
            // 插入新行
            // *关键修改*：insertRow 会把下面的推下去，但不会带样式。
            // 我们插入一行，然后把 templateRow 的样式刷给它
            currentRow = worksheet.insertRow(currentRowIdx, new Array(headerRow.cellCount).fill(null));
            
            // 复制行高
            if (templateRow.height) currentRow.height = templateRow.height;
            
            // 逐单元格复制样式 (Borders, fills, fonts, alignments)
            templateRow.eachCell({ includeEmpty: true }, (srcCell, colNum) => {
              const destCell = currentRow.getCell(colNum);
              destCell.style = Object.assign({}, srcCell.style); // Shallow copy of style object works mostly
              
              // 复制 DataValidation
              if (srcCell.dataValidation) destCell.dataValidation = srcCell.dataValidation;
            });
          }

          // 填值
          for (const targetField in fieldMapping.value) {
            const sourceField = fieldMapping.value[targetField];
            if (!sourceField) continue;
            
            const colIdx = colMap[targetField];
            if (!colIdx) continue;

            const targetCell = currentRow.getCell(colIdx);
            
            // ★ 特殊处理：货箱编号/货箱编码 字段
            if (targetField === '货箱编号*' || targetField === '货箱编码*') {
              // 获取 FBA编号 和 箱数
              const fbaCode = String(rowA['FBA编号'] || rowA[sourceField] || '');
              const boxCountRaw = rowA['箱数'];
              const boxCount = parseInt(String(boxCountRaw), 10) || 1;
              
              // 应用转换规则
              const newBoxNumber = generateBoxNumber(fbaCode, boxCount);
              targetCell.value = newBoxNumber;
              console.log(`货箱编号转换: FBA=${fbaCode}, 箱数=${boxCount} -> ${newBoxNumber}`);
            }
            // ★ 特殊处理：长宽高拆分
            // A表的 "材积CM(长*宽*高)" 格式如 "52*51*28" 需要拆分到 B/C 表的三个字段
            else if (/长.*\(CM\)|宽.*\(CM\)|高.*\(CM\)/i.test(targetField) || 
                     /长.*（CM）|宽.*（CM）|高.*（CM）/i.test(targetField) ||
                     targetField === '长(CM)' || targetField === '宽(CM)' || targetField === '高(CM)' ||
                     targetField === '货箱长度(CM)*' || targetField === '货箱宽度(CM)*' || targetField === '货箱高度(CM)*' ||
                     targetField === '外箱长(CM)' || targetField === '外箱宽(CM)' || targetField === '外箱高(CM)') {
              
              const isLength = targetField.includes('长');
              const isWidth = targetField.includes('宽');
              const isHeight = targetField.includes('高');

              // 优先从 "材积CM(长*宽*高)" 获取数据
              const dimensionStr = String(rowA['材积CM(长*宽*高)'] || rowA[sourceField] || '');
              // 支持多种分隔符：* 或 x 或 X 或 ×
              const parts = dimensionStr.split(/[*xX×]/);
              
              let value = '';
              if (isLength && parts[0]) {
                value = parts[0].trim();
              } else if (isWidth && parts[1]) {
                value = parts[1].trim();
              } else if (isHeight && parts[2]) {
                value = parts[2].trim();
              }
              
              targetCell.value = value ? parseFloat(value) || value : '';
              console.log(`尺寸拆分: "${dimensionStr}" -> ${targetField} = "${value}"`);
            } else {
              // 普通字段直接赋值
              targetCell.value = rowA[sourceField];
            }

            // ★ 设置单元格对齐方式：水平居中 + 垂直居中
            targetCell.alignment = {
              horizontal: 'center',
              vertical: 'middle',
              wrapText: true  // 自动换行
            };

            // ★ 图片 Image Transfer
            // 检查 SourceFile 是否有图片在这一行、这一列(sourceField)
            if (sourceFile.images[i]) {
                const imgs = sourceFile.images[i] as any[];
                // 找属于这个 sourceField 的图片
                const matchedImg = imgs.find(img => img.header === sourceField);
                if (matchedImg) {
                    let imageBuffer: ArrayBuffer | null = null;
                    let imageExtension = 'png';
                    
                    // 处理 Excel 365 单元格内嵌图片 (DISPIMG)
                    if (matchedImg.type === 'cellImage' && matchedImg.cellImage) {
                        imageBuffer = matchedImg.cellImage.buffer;
                        imageExtension = matchedImg.cellImage.extension;
                        console.log(`Found DISPIMG image for ${sourceField}, size: ${imageBuffer.byteLength}`);
                    }
                    // 处理传统浮动图片
                    else if (matchedImg.type === 'floating' && sourceFile.workbook) {
                        try {
                            const media = sourceFile.workbook.getImage(Number(matchedImg.imageId));
                            if (media) {
                                imageBuffer = media.buffer;
                                imageExtension = media.extension;
                            } else {
                                const fallbackMedia = sourceFile.workbook.model.media?.find((m: any) => String(m.index) === String(matchedImg.imageId));
                                if (fallbackMedia) {
                                  imageBuffer = fallbackMedia.buffer;
                                  imageExtension = fallbackMedia.extension;
                                }
                            }
                        } catch (e) {
                            console.error('Error fetching floating image', e);
                        }
                    }
                    
                    // 如果找到了图片数据，插入到目标工作簿
                    if (imageBuffer) {
                        const imageId = workbook.addImage({
                            buffer: imageBuffer as Buffer,
                            extension: imageExtension as 'png' | 'jpeg' | 'gif',
                        });
                        
                        // 设置单元格宽高以容纳图片
                        const col = worksheet.getColumn(colIdx);
                        if (!col.width || col.width < 15) col.width = 15;
                        currentRow.height = 80; // 设置行高
                        
                        // 使用 tl + ext 指定图片尺寸，保持纵横比
                        worksheet.addImage(imageId, {
                            tl: { col: colIdx - 1 + 0.1, row: currentRowIdx - 1 + 0.1 },
                            ext: { width: 80, height: 80 } // 固定尺寸，像素
                        });
                        
                        // 清空文字值，避免遮挡图片
                        targetCell.value = '';
                        console.log(`Image inserted at row ${currentRowIdx}, col ${colIdx}`);
                    }
                }
            }
          }
          currentRow.commit();
        }
      } // end if rows > 0

      // ★ 生成 Excel Buffer 并添加到 Zip
      // ★ 获取文件名：第一行 FBA 编码 + _模版名称 (如 FBA12345_星夜.xlsx)
      const templateName = getTemplateName();
      const outputName = `${firstRowFbaCode || sourceFile.warehouseCode || 'Unknown'}_${templateName}.xlsx`;
      
      const buffer = await workbook.xlsx.writeBuffer();
      outputZip.file(outputName, buffer);
      console.log(`生成文件: ${outputName}`);

    } // end for sourceFiles

    const content = await outputZip.generateAsync({ type: "blob" });
    saveAs(content, `批量转换结果_${new Date().getTime()}.zip`);

  } catch (e: any) {
    console.error(e);
    alert(`错误: ${e.message}`);
  } finally {
    isProcessing.value = false;
  }
};

</script>

<template>
  <div class="min-h-screen bg-slate-50 font-sans text-slate-800 selection:bg-blue-100">
    <!-- Navbar -->
    <nav class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm sticky top-0 z-10">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">Ex</div>
        <span class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-700 to-indigo-600">
          智能转单工具
        </span>
      </div>
      <div class="text-xs font-medium px-3 py-1 bg-blue-50 text-blue-700 rounded-full border border-blue-100">
        客服专用版 v2.0 (Batch)
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-6 py-8">
      
      <!-- Step 1: Upload Files -->
      <transition 
        enter-active-class="transition duration-500 ease-out" 
        enter-from-class="opacity-0 translate-y-4" 
        enter-to-class="opacity-100 translate-y-0"
      >
      <div v-if="step === 1" class="space-y-8">
        <div class="text-center space-y-2 mb-10">
          <h2 class="text-3xl font-bold text-slate-900">批量数据转换</h2>
          <p class="text-slate-500">第一步：请上传源文件（明日之星）和 目标模版（星夜/亿阳）</p>
          <p class="text-xs text-slate-400 bg-yellow-50 inline-block px-2 py-1 rounded border border-yellow-200">
            支持只读模式，完美保留模版格式和公式
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <!-- A File Upload (Multi) -->
          <div class="flex flex-col gap-4">
            <div 
              class="relative group rounded-2xl border-2 border-dashed transition-all duration-300 min-h-[300px] flex flex-col items-center justify-center cursor-pointer overflow-hidden bg-white"
              :class="[
                isDraggingA ? 'border-blue-500 bg-blue-50/50 scale-[1.02]' : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50',
                sourceFiles.length > 0 ? 'border-blue-500 border-solid bg-blue-50/10' : ''
              ]"
              @dragover.prevent="isDraggingA = true"
              @dragleave.prevent="isDraggingA = false"
              @drop.prevent="(e) => { isDraggingA = false; handleFilesA(e.dataTransfer?.files || null); }"
              @click="$refs.inputA.click()"
            >
              <input type="file" ref="inputA" class="hidden" accept=".xls,.xlsx,.zip" multiple @change="(e:any) => handleFilesA(e.target.files)" />
              
              <div v-if="sourceFiles.length === 0" class="text-center p-8 space-y-4">
                <div class="w-16 h-16 bg-blue-100 text-blue-600 rounded-2xl mx-auto flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
                </div>
                <h3 class="text-xl font-semibold text-slate-800">上传 明日之星 表格</h3>
                <p class="text-sm text-slate-400">支持拖拽多个文件或 Zip 压缩包</p>
              </div>
              
              <div v-else class="text-center p-8 z-10 w-full">
                <div class="w-16 h-16 bg-blue-100 text-blue-600 rounded-full mx-auto flex items-center justify-center mb-4">
                   <span class="text-2xl font-bold">{{ sourceFiles.length }}</span>
                </div>
                <h3 class="text-xl font-semibold text-slate-800">已选择 {{ sourceFiles.length }} 个文件</h3>
                <p class="text-sm text-slate-500 mt-2">点击继续添加</p>
              </div>
              
              <div class="absolute top-4 left-4 font-bold text-6xl text-slate-100 pointer-events-none select-none">A</div>
            </div>
            
            <!-- File List Preview -->
            <div v-if="sourceFiles.length > 0" class="bg-white rounded-xl border border-slate-200 p-4 max-h-[200px] overflow-y-auto shadow-sm">
               <h4 class="text-xs font-bold text-slate-400 uppercase mb-2 tracking-wider">文件列表</h4>
               <ul class="space-y-2">
                 <li v-for="(f, idx) in sourceFiles" :key="idx" class="flex items-center justify-between text-sm p-2 bg-slate-50 rounded hover:bg-slate-100 transition-colors">
                    <span class="truncate flex-1 max-w-[200px]" :title="f.name">{{ f.name }}</span>
                    <div class="flex items-center gap-3">
                       <span class="text-xs text-slate-400 font-mono">{{ f.warehouseCode || '无仓库码' }}</span>
                       <button @click.stop="removeSourceFile(idx)" class="text-slate-400 hover:text-red-500">
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
                       </button>
                    </div>
                 </li>
               </ul>
            </div>
          </div>

          <!-- Target Upload (Single) -->
          <div 
            class="relative group rounded-2xl border-2 border-dashed transition-all duration-300 min-h-[300px] flex flex-col items-center justify-center cursor-pointer overflow-hidden bg-white"
            :class="[
              isDraggingTarget ? 'border-purple-500 bg-purple-50/50 scale-[1.02]' : 'border-slate-300 hover:border-purple-400 hover:bg-slate-50',
              fileTarget ? 'border-purple-500 border-solid bg-purple-50/30' : ''
            ]"
            @dragover.prevent="isDraggingTarget = true"
            @dragleave.prevent="isDraggingTarget = false"
            @drop.prevent="(e) => { isDraggingTarget = false; if(e.dataTransfer?.files[0]) handleFileTarget(e.dataTransfer.files[0]); }"
            @click="$refs.inputTarget.click()"
          >
             <input type="file" ref="inputTarget" class="hidden" accept=".xls,.xlsx" @change="(e:any) => handleFileTarget(e.target.files[0])" />
            
             <div v-if="!fileTarget" class="text-center p-8 space-y-4">
              <div class="w-16 h-16 bg-purple-100 text-purple-600 rounded-2xl mx-auto flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
              </div>
              <h3 class="text-xl font-semibold text-slate-800">上传模版（星夜 或 亿阳）</h3>
              <p class="text-sm text-slate-400">将用于所有源文件的转换</p>
            </div>

             <div v-else class="text-center p-8 z-10">
               <div class="w-16 h-16 bg-green-100 text-green-600 rounded-full mx-auto flex items-center justify-center mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-8 h-8"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              </div>
              <h3 class="text-xl font-semibold text-slate-800 truncate max-w-[200px]">{{ fileNameTarget }}</h3>
              <p class="text-sm text-green-600 font-medium mt-1">模版就绪</p>
               <div class="mt-4 text-xs text-slate-500 bg-white px-3 py-1 rounded border border-slate-200 inline-block">
                类型: <span class="font-bold text-purple-600 text-sm">{{ targetType === 'B' ? '星夜' : targetType === 'C' ? '亿阳' : targetType }}</span>
              </div>
            </div>
            
             <div class="absolute top-4 left-4 font-bold text-6xl text-slate-100 pointer-events-none select-none">T</div>
          </div>
        </div>

        <div class="flex justify-center pt-8">
          <button 
            @click="step = 2"
            :disabled="!canNextStep"
            class="px-8 py-3 bg-blue-600 text-white rounded-xl font-bold text-lg shadow-lg hover:bg-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            下一步：配置映射
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" /></svg>
          </button>
        </div>
      </div>
      </transition>

      <!-- Step 2: Mapping -->
      <transition 
        enter-active-class="transition duration-500 ease-out" 
        enter-from-class="opacity-0 translate-y-4" 
        enter-to-class="opacity-100 translate-y-0"
      >
      <div v-if="step === 2" class="max-w-5xl mx-auto">
        <div class="flex items-center justify-between mb-6">
           <div>
            <h2 class="text-2xl font-bold text-slate-800">字段映射配置</h2>
            <p class="text-slate-500 text-sm mt-1">此配置将应用于所有 <strong>{{ sourceFiles.length }}</strong> 个文件</p>
           </div>
           
           <div class="flex gap-3">
             <input type="file" ref="importTemplateInput" class="hidden" accept=".json" @change="handleImportTemplate" />
             <button @click="$refs.importTemplateInput.click()" class="px-4 py-2 text-sm bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 font-medium flex items-center gap-2">
                导入配置
             </button>
             <button @click="exportTemplate" class="px-4 py-2 text-sm bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 font-medium flex items-center gap-2">
                导出配置
             </button>
           </div>
        </div>

        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div class="bg-slate-50 px-6 py-4 border-b border-slate-200 grid grid-cols-12 gap-4 text-sm font-semibold text-slate-500">
             <div class="col-span-5">目标字段 ({{ targetType === 'B' ? '星夜' : targetType === 'C' ? '亿阳' : targetType }})</div>
             <div class="col-span-2 text-center flex items-center justify-center">→</div>
             <div class="col-span-5">来源字段 (明日之星)</div>
          </div>
          
          <div class="max-h-[55vh] overflow-y-auto p-6 space-y-3 bg-slate-50/50">
             <div v-for="targetField in headersTarget" :key="targetField" class="grid grid-cols-12 gap-4 items-center group">
               <div class="col-span-5">
                 <div class="bg-white border border-slate-200 rounded-lg p-3 text-sm font-medium text-slate-700 shadow-sm flex items-center justify-between">
                    <span>{{ targetField }}</span>
                    <span class="text-xs text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">Target</span>
                 </div>
               </div>
               <div class="col-span-2 flex justify-center text-slate-300 group-hover:text-blue-500 transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5"><path fill-rule="evenodd" d="M12.232 4.232a2.5 2.5 0 013.536 3.536l-1.225 1.224a.75.75 0 001.061 1.06l1.224-1.224a4 4 0 00-5.656-5.656l-3 3a4 4 0 00.225 5.865.75.75 0 00.977-1.138 2.5 2.5 0 01-.142-3.667l3-3z" clip-rule="evenodd" /><path fill-rule="evenodd" d="M11.603 7.963a.75.75 0 00-.977 1.138 2.5 2.5 0 01.142 3.667l-3 3a2.5 2.5 0 01-3.536-3.536l1.225-1.224a.75.75 0 00-1.061-1.06l-1.224 1.224a4 4 0 105.656 5.656l3-3a4 4 0 00-.225-5.865z" clip-rule="evenodd" /></svg>
               </div>
               <div class="col-span-5">
                 <select 
                   v-model="fieldMapping[targetField]" 
                   class="w-full bg-white border border-slate-300 text-slate-700 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-3 shadow-sm hover:border-blue-400 transition-colors"
                 >
                   <option value="">(忽略此字段)</option>
                   <option v-for="headerA in headersA" :key="headerA" :value="headerA">{{ headerA }}</option>
                 </select>
               </div>
             </div>
          </div>
        </div>
        
        <div class="mt-8 flex justify-between items-center bg-white p-6 rounded-xl shadow-lg border border-slate-100">
           <div class="flex items-center gap-4 text-sm text-slate-500">
              <span class="bg-blue-100 text-blue-700 px-2 py-1 rounded font-bold">{{ sourceFiles.length }} 个文件待处理</span>
           </div>

           <div class="flex gap-4">
              <button @click="step = 1" class="px-6 py-2.5 text-slate-500 font-medium hover:bg-slate-50 rounded-lg transition-colors">上一步</button>
              <button 
                @click="processConversion" 
                :disabled="isProcessing"
                class="px-8 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-lg shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all flex items-center gap-2 disabled:opacity-70 disabled:cursor-wait"
              >
                 <svg v-if="!isProcessing" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" /></svg>
                 <svg v-else class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                 {{ isProcessing ? '正在处理...' : '批量转换并打包下载' }}
              </button>
           </div>
        </div>
      </div>
      </transition>
    </main>
  </div>
</template>
