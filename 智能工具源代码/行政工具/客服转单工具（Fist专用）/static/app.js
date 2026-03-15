const state = {
  headers: [],
  targets: [],
  mappingRows: [],
};

const aFileInput = document.getElementById("aFile");
const bFileInput = document.getElementById("bFile");
const aFileCard = document.getElementById("aFileCard");
const bFileCard = document.getElementById("bFileCard");
const aFileName = document.getElementById("aFileName");
const bFileName = document.getElementById("bFileName");
const fileStatus = document.getElementById("fileStatus");
const mappingStatus = document.getElementById("mappingStatus");
const inspectButton = document.getElementById("inspectButton");
const addMappingButton = document.getElementById("addMappingButton");
const exportConfigButton = document.getElementById("exportConfigButton");
const importConfigInput = document.getElementById("importConfigInput");
const generateButton = document.getElementById("generateButton");
const mappingList = document.getElementById("mappingList");
const rowTemplate = document.getElementById("mappingRowTemplate");
const statusCard = document.getElementById("statusCard");
const resultCard = document.getElementById("resultCard");

aFileInput.addEventListener("change", () => {
  aFileName.textContent = aFileInput.files[0]?.name || "未选择文件";
  updateFileSelectionState();
});

bFileInput.addEventListener("change", () => {
  bFileName.textContent = bFileInput.files[0]?.name || "未选择文件";
  updateFileSelectionState();
});

inspectButton.addEventListener("click", inspectFiles);
addMappingButton.addEventListener("click", () => addMappingRow());
exportConfigButton.addEventListener("click", exportConfig);
importConfigInput.addEventListener("change", importConfig);
generateButton.addEventListener("click", generateFiles);

addMappingRow();
addMappingRow();
updateFileSelectionState();

async function inspectFiles() {
  if (!aFileInput.files[0] || !bFileInput.files[0]) {
    setStatus("请先选择 A 表和 B 表。", true);
    setFileStatus("还缺少文件，请确认 A 表和 B 表都已选择。", true);
    return;
  }

  setStatus("正在读取字段...", false);
  setFileStatus("文件已选齐，正在读取字段。", false);
  setMappingStatus("正在读取字段...", false);
  try {
    const payload = {
      aFileName: aFileInput.files[0].name,
      aFileContent: await fileToBase64(aFileInput.files[0]),
      bFileName: bFileInput.files[0].name,
      bFileContent: await fileToBase64(bFileInput.files[0]),
    };
    const response = await fetch("/api/inspect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "读取字段失败");
    }

    state.headers = data.headers.filter(Boolean);
    state.targets = data.targets;
    state.mappingRows.forEach((row) => refreshRowOptions(row));
    setStatus(`字段读取完成：A 表 ${state.headers.length} 个字段，B 表 ${state.targets.length} 个目标位。`, false);
    setMappingStatus(`字段读取完成：A 表 ${state.headers.length} 个字段，B 表 ${state.targets.length} 个目标位。`, false);
    updateActionState();
  } catch (error) {
    setStatus(error.message, true);
    setMappingStatus(error.message, true);
  }
}

function addMappingRow(sourceHeader = "", targetCell = "") {
  if (state.mappingRows.length >= 30) {
    setStatus("最多只能配置 30 条映射。", true);
    setMappingStatus("最多只能配置 30 条映射。", true);
    return;
  }

  const row = rowTemplate.content.firstElementChild.cloneNode(true);
  const sourceSelect = row.querySelector(".source-select");
  const targetSelect = row.querySelector(".target-select");
  const removeButton = row.querySelector(".remove-button");

  removeButton.addEventListener("click", () => {
    row.remove();
    state.mappingRows = state.mappingRows.filter((item) => item.row !== row);
  });

  mappingList.appendChild(row);
  const record = { row, sourceSelect, targetSelect };
  state.mappingRows.push(record);
  refreshRowOptions(record, sourceHeader, targetCell);
}

function refreshRowOptions(record, sourceHeader = record.sourceSelect.value, targetCell = record.targetSelect.value) {
  const currentSource = sourceHeader;
  const currentTarget = targetCell;

  record.sourceSelect.innerHTML = '<option value="">选择 A 表字段</option>';
  record.targetSelect.innerHTML = '<option value="">选择 B 表字段</option>';

  state.headers.forEach((header, index) => {
    const columnLabel = indexToColumn(index + 1);
    const option = document.createElement("option");
    option.value = header;
    option.textContent = `${header} (${columnLabel})`;
    option.selected = header === currentSource;
    record.sourceSelect.appendChild(option);
  });

  state.targets.forEach((target) => {
    const option = document.createElement("option");
    option.value = target.cell;
    option.textContent = `${target.label} [${target.cell}]`;
    option.selected = target.cell === currentTarget;
    record.targetSelect.appendChild(option);
  });
}

function indexToColumn(index) {
  let result = "";
  let current = index;
  while (current > 0) {
    const remainder = (current - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    current = Math.floor((current - 1) / 26);
  }
  return result;
}

function exportConfig() {
  const mappings = collectMappings();
  if (!mappings.length) {
    setStatus("当前没有可导出的映射配置。", true);
    return;
  }

  const content = {
    version: 1,
    exportedAt: new Date().toISOString(),
    mappings,
  };
  const blob = new Blob([JSON.stringify(content, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "mapping-config.json";
  link.click();
  URL.revokeObjectURL(url);
  setStatus("映射配置已导出。", false);
}

async function importConfig(event) {
  const file = event.target.files[0];
  if (!file) {
    return;
  }

  try {
    const content = JSON.parse(await file.text());
    const mappings = content.mappings || [];
    mappingList.innerHTML = "";
    state.mappingRows = [];
    mappings.slice(0, 30).forEach((mapping) => addMappingRow(mapping.source_header, mapping.target_cell));
    if (!mappings.length) {
      addMappingRow();
    }
    setStatus("映射配置已导入。读取完字段后会自动匹配下拉选项。", false);
    setMappingStatus("映射配置已导入。读取完字段后会自动匹配下拉选项。", false);
  } catch (error) {
    setStatus(`导入配置失败: ${error.message}`, true);
    setMappingStatus(`导入配置失败: ${error.message}`, true);
  } finally {
    event.target.value = "";
  }
}

async function generateFiles() {
  if (!aFileInput.files[0] || !bFileInput.files[0]) {
    setStatus("请先选择 A 表和 B 表。", true);
    setFileStatus("还缺少文件，请确认 A 表和 B 表都已选择。", true);
    return;
  }

  const mappings = collectMappings();
  setStatus("正在生成文件，请稍候...", false);
  resultCard.classList.add("hidden");

  try {
    const payload = {
      aFileName: aFileInput.files[0].name,
      aFileContent: await fileToBase64(aFileInput.files[0]),
      bFileName: bFileInput.files[0].name,
      bFileContent: await fileToBase64(bFileInput.files[0]),
      mappings,
    };
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "生成失败");
    }

    resultCard.innerHTML = `
      <h3>生成完成</h3>
      <p>共生成 <strong>${data.count}</strong> 个 Excel 文件。</p>
      <p>输出目录：<code>${escapeHtml(data.outputDir)}</code></p>
      <p><a href="${data.zipUrl}" target="_blank" rel="noreferrer">下载打包 ZIP</a></p>
      <div class="result-files">${data.files.map((file) => `<span>${escapeHtml(file)}</span>`).join("")}</div>
    `;
    resultCard.classList.remove("hidden");
    setStatus("文件生成完成。你可以直接下载 ZIP，也可以去输出目录查看单个 Excel。", false);
  } catch (error) {
    setStatus(error.message, true);
  }
}

function collectMappings() {
  return state.mappingRows
    .map((item) => {
      const target = state.targets.find((entry) => entry.cell === item.targetSelect.value);
      return {
        source_header: item.sourceSelect.value,
        target_cell: item.targetSelect.value,
        target_label: target?.label || item.targetSelect.value,
      };
    })
    .filter((item) => item.source_header && item.target_cell);
}

function setStatus(message, isError) {
  statusCard.innerHTML = `<p>${escapeHtml(message)}</p>`;
  statusCard.classList.toggle("is-error", Boolean(isError));
}

function setFileStatus(message, isError) {
  fileStatus.textContent = message;
  fileStatus.classList.toggle("is-error", Boolean(isError));
}

function setMappingStatus(message, isError) {
  mappingStatus.textContent = message;
  mappingStatus.classList.toggle("is-error", Boolean(isError));
}

function updateFileSelectionState() {
  const hasA = Boolean(aFileInput.files[0]);
  const hasB = Boolean(bFileInput.files[0]);
  aFileCard.classList.toggle("is-ready", hasA);
  bFileCard.classList.toggle("is-ready", hasB);

  if (!hasA && !hasB) {
    setFileStatus("请先同时选择 A 表和 B 表，随后点击“读取字段”。", false);
  } else if (!hasA) {
    setFileStatus("A 表还没有选中，请先选择 A 表。", true);
  } else if (!hasB) {
    setFileStatus("B 表还没有选中，请先选择 B 表。", true);
  } else {
    setFileStatus("A 表和 B 表已选中，可以点击“读取字段”。", false);
  }

  updateActionState();
}

function updateActionState() {
  const hasA = Boolean(aFileInput.files[0]);
  const hasB = Boolean(bFileInput.files[0]);
  const hasLoadedFields = state.headers.length > 0 && state.targets.length > 0;

  inspectButton.disabled = !(hasA && hasB);
  generateButton.disabled = !(hasA && hasB && hasLoadedFields);
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result);
      resolve(result.split(",", 2)[1] || "");
    };
    reader.onerror = () => reject(new Error("文件读取失败"));
    reader.readAsDataURL(file);
  });
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
