(function () {
  const FOOTER_MARKERS = ['出货日期', '审核', '确认', '签字', '签名', '合计', '总计'];
  const IMPORT_FIELD_DEFINITIONS = [
    { key: 'reference', label: '货号 / SKU', description: '可选，用于导入后回看来源。' },
    { key: 'productName', label: '品名', description: '可选，仅做辅助识别。' },
    { key: 'declaredPrice', label: '申报价值', description: '可选，不参与当前费用计算。' },
    { key: 'boxCount', label: '箱数', description: '必填，决定整组箱量。', required: true },
    { key: 'piecesPerBox', label: '每箱件数', description: '优先映射；如只给总件数，会自动按箱数拆分。', required: true },
    { key: 'totalPieces', label: '总件数', description: '选填，可在缺少每箱件数时参与换算。' },
    { key: 'skuCount', label: '每箱 SKU 数', description: '选填；不映射时可用默认值补齐。' },
    { key: 'actualWeightKg', label: '单箱重量 (KG)', description: '必填；不映射时可用默认值补齐。', required: true },
    { key: 'dimensions', label: '组合尺寸列', description: '如 “62*47.5*59”，会自动拆成长宽高。', required: true },
    { key: 'lengthCm', label: '箱长 (CM)', description: '如果客户已拆列，可单独映射。', required: true },
    { key: 'widthCm', label: '箱宽 (CM)', description: '如果客户已拆列，可单独映射。', required: true },
    { key: 'heightCm', label: '箱高 (CM)', description: '如果客户已拆列，可单独映射。', required: true }
  ];

  const FIELD_ALIASES = {
    reference: ['货号', 'sku', '编号', '产品编码', 'item'],
    productName: ['品名', '产品名称', '货物名称', 'name'],
    declaredPrice: ['申报价', '申报价值', 'value', 'price'],
    boxCount: ['总箱数', '箱数', 'ctn', 'carton'],
    piecesPerBox: ['单箱个数', '每箱个数', '每箱件数', '装箱数', 'pcs/ctn'],
    totalPieces: ['总个数', '总件数', '数量', 'totalpcs'],
    skuCount: ['每箱sku数', 'sku数', 'skuqty', 'skucount'],
    actualWeightKg: ['单箱重量', '毛重', '净重', '重量', 'kg'],
    dimensions: ['外箱尺寸（厘米）', '外箱尺寸', '箱规', '长宽高', '尺寸', 'cm'],
    lengthCm: ['箱长', '长'],
    widthCm: ['箱宽', '宽'],
    heightCm: ['箱高', '高']
  };

  function toTrimmedString(value) {
    if (value === null || value === undefined) return '';
    return String(value).trim();
  }

  function parseNumericValue(value) {
    if (typeof value === 'number') {
      return Number.isFinite(value) ? value : null;
    }

    const text = toTrimmedString(value)
      .replace(/,/g, '')
      .replace(/US\$/gi, '')
      .replace(/\$/g, '');
    if (!text) return null;

    const numeric = Number(text);
    return Number.isFinite(numeric) ? numeric : null;
  }

  function normalizeHeader(header) {
    return toTrimmedString(header).toLowerCase().replace(/\s+/g, '');
  }

  function isBlankRow(row) {
    return row.every((cell) => toTrimmedString(cell) === '');
  }

  function isFooterLikeRow(row) {
    const joined = row.map(toTrimmedString).filter(Boolean).join(' ');
    if (!joined) return false;
    return FOOTER_MARKERS.some((marker) => joined.includes(marker));
  }

  function getColumnValue(headers, row, columnName) {
    if (!columnName) return undefined;
    const index = headers.findIndex((header) => header === columnName);
    return index >= 0 ? row[index] : undefined;
  }

  function getRequiredIssues(boxGroup) {
    const issues = [];

    if (!boxGroup.boxCount || boxGroup.boxCount <= 0) issues.push('缺少箱数');
    if (!boxGroup.piecesPerBox || boxGroup.piecesPerBox <= 0) issues.push('缺少每箱件数');
    if (boxGroup.actualWeightKg === null || boxGroup.actualWeightKg <= 0) issues.push('缺少单箱重量');
    if (boxGroup.lengthCm === null || boxGroup.lengthCm <= 0) issues.push('缺少箱长');
    if (boxGroup.widthCm === null || boxGroup.widthCm <= 0) issues.push('缺少箱宽');
    if (boxGroup.heightCm === null || boxGroup.heightCm <= 0) issues.push('缺少箱高');

    return issues;
  }

  function parseDimensionValue(value) {
    const text = toTrimmedString(value);
    if (!text) return null;

    const numbers = text.match(/-?\d+(?:\.\d+)?/g);
    if (!numbers || numbers.length < 3) return null;

    const [lengthCm, widthCm, heightCm] = numbers.slice(0, 3).map(Number);
    if (![lengthCm, widthCm, heightCm].every(Number.isFinite)) return null;

    return { lengthCm, widthCm, heightCm };
  }

  function suggestMapping(headers) {
    const normalizedHeaders = headers.map((header) => ({
      raw: header,
      normalized: normalizeHeader(header)
    }));

    return Object.entries(FIELD_ALIASES).reduce((acc, [fieldKey, aliases]) => {
      for (const alias of aliases) {
        const normalizedAlias = alias.replace(/\s+/g, '').toLowerCase();
        const match = normalizedHeaders.find((header) => header.normalized.includes(normalizedAlias));
        if (match) {
          acc[fieldKey] = match.raw;
          break;
        }
      }
      return acc;
    }, {});
  }

  function mapWorksheetRows(input) {
    const { headers, rows, mapping, defaults } = input;
    const result = {
      validRows: [],
      incompleteRows: [],
      skippedRows: []
    };

    rows.forEach((row, index) => {
      const rowNumber = index + 2;
      const rawReference = toTrimmedString(getColumnValue(headers, row, mapping.reference));
      const rawProductName = toTrimmedString(getColumnValue(headers, row, mapping.productName));
      const rawDeclaredPrice = parseNumericValue(getColumnValue(headers, row, mapping.declaredPrice));
      const boxCount = parseNumericValue(getColumnValue(headers, row, mapping.boxCount)) ?? 0;
      const piecesPerBox =
        parseNumericValue(getColumnValue(headers, row, mapping.piecesPerBox)) ??
        (() => {
          const totalPieces = parseNumericValue(getColumnValue(headers, row, mapping.totalPieces));
          return totalPieces && boxCount > 0 ? totalPieces / boxCount : 0;
        })();
      const skuCount = parseNumericValue(getColumnValue(headers, row, mapping.skuCount)) ?? defaults.skuCount ?? 1;
      const actualWeightKg =
        parseNumericValue(getColumnValue(headers, row, mapping.actualWeightKg)) ?? defaults.actualWeightKg ?? null;

      const parsedDimensions = parseDimensionValue(getColumnValue(headers, row, mapping.dimensions));
      const lengthCm = parseNumericValue(getColumnValue(headers, row, mapping.lengthCm)) ?? parsedDimensions?.lengthCm ?? null;
      const widthCm = parseNumericValue(getColumnValue(headers, row, mapping.widthCm)) ?? parsedDimensions?.widthCm ?? null;
      const heightCm = parseNumericValue(getColumnValue(headers, row, mapping.heightCm)) ?? parsedDimensions?.heightCm ?? null;

      const boxGroup = {
        boxCount,
        piecesPerBox,
        skuCount,
        actualWeightKg,
        lengthCm,
        widthCm,
        heightCm,
        reference: rawReference || undefined,
        productName: rawProductName || undefined,
        declaredPrice: rawDeclaredPrice,
        sourceRowNumber: rowNumber
      };

      const mappedRow = {
        rowNumber,
        boxGroup,
        issues: [],
        rawRow: row
      };

      if (isBlankRow(row) || (isFooterLikeRow(row) && boxCount <= 0 && piecesPerBox <= 0)) {
        mappedRow.issues = ['已跳过非数据行'];
        result.skippedRows.push(mappedRow);
        return;
      }

      mappedRow.issues = getRequiredIssues(boxGroup);

      if (mappedRow.issues.length > 0) {
        result.incompleteRows.push(mappedRow);
        return;
      }

      result.validRows.push(mappedRow);
    });

    return result;
  }

  async function readWorkbookFromFile(file) {
    if (!window.XLSX) {
      throw new Error('未检测到 XLSX 解析库，请确认 vendor/xlsx.full.min.js 已正确加载。');
    }

    const buffer = await file.arrayBuffer();
    return window.XLSX.read(buffer, { type: 'array' });
  }

  function getSheetRows(workbook, sheetName) {
    const targetSheetName = sheetName || workbook.SheetNames[0];
    const sheet = workbook.Sheets[targetSheetName];
    if (!sheet) {
      throw new Error(`未找到工作表：${targetSheetName}`);
    }

    const sheetRows = window.XLSX.utils.sheet_to_json(sheet, {
      header: 1,
      raw: false,
      defval: ''
    });

    if (!sheetRows.length) {
      return { headers: [], rows: [] };
    }

    const [headerRow, ...rows] = sheetRows;
    const headers = Array.isArray(headerRow) ? headerRow.map((cell) => toTrimmedString(cell)) : [];

    return { headers, rows };
  }

  window.ExcelImportRuntime = {
    IMPORT_FIELD_DEFINITIONS,
    parseDimensionValue,
    suggestMapping,
    mapWorksheetRows,
    readWorkbookFromFile,
    getSheetRows
  };
})();
