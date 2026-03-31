<script setup lang="ts">
import { ref, reactive } from 'vue';
import { ElMessage } from 'element-plus';
import { saveAs } from 'file-saver';
import { ExcelParser } from './core/ExcelParser';
import { Generator } from './core/Generator';
import type { RowWithImages, ColumnMapping, TemplateConfig } from './types/OrderData';

// State
const step = ref(1);
const isProcessing = ref(false);
const logs = ref<{ time: string; msg: string; type: string }[]>([]);

// Template Data
const templateFile = ref<File | null>(null);
const templateColumns = ref<ColumnMapping[]>([]);
const warehouseMap = ref<Record<string, any[]>>({});

// Data Source
const dataHeaders = ref<string[]>([]);
const mergedData = ref<RowWithImages[]>([]);

// Config
const config = reactive<TemplateConfig>({
  groupBy: '',
  sumBy: '',
  declareType: '单独报关件'
});

const mapping = reactive<Record<string, any>>({});

// Export/Import Configuration
const exportConfig = () => {
    const data = {
        mapping: { ...mapping },
        config: { ...config }
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    saveAs(blob, `fba_config_${new Date().toISOString().slice(0, 10)}.json`);
    addLog('配置已导出', 'info');
};

const handleConfigImport = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target?.result as string);
            if (data.mapping) Object.assign(mapping, data.mapping);
            if (data.config) Object.assign(config, data.config);
            addLog('配置已导入', 'info');
            ElMessage.success('配置导入成功');
        } catch (err) {
            ElMessage.error('配置文件格式错误');
        }
    };
    reader.readAsText(file);
    return false;
};

const isDimensionCol = (name: string) => name.includes('材积') || (name.includes('长') && name.includes('宽') && name.includes('高'));


// Methods
const addLog = (msg: string, type: 'info' | 'warn' | 'error' = 'info') => {
  const time = new Date().toLocaleTimeString();
  logs.value.push({ time, msg, type });
};

const handleTemplateUpload = async (file: File) => {
  if (!file) return;
  try {
    const cols = await ExcelParser.parseTemplateHeaders(file, 11); // Row 11 is header
    const whMap = await ExcelParser.parseHiddenWarehouseSheet(file);
    
    templateFile.value = file;
    templateColumns.value = cols;
    warehouseMap.value = whMap;
    
    step.value = 2;
    addLog(`模板已加载: ${file.name}`, 'info');
    if (Object.keys(whMap).length > 0) {
        addLog(`⚡ 已自动识别隐藏仓库表，含 ${Object.keys(whMap).length} 条地址数据`, 'info');
    }
  } catch (e: any) {
    ElMessage.error(e.message);
    addLog(e.message, 'error');
  }
};

const handleDataUpload = async (files: FileList | null) => {
  if (!files || files.length === 0) return;
  isProcessing.value = true;
  addLog(`正在解析 ${files.length} 个数据文件...`, 'info');

  try {
    let allData: RowWithImages[] = [];
    let headers = new Set<string>();

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (!file) continue;
        const res = await ExcelParser.parseDataSource(file);
        
        // Merge headers
        res.headers.forEach(h => headers.add(h));
        // Merge data
        allData = allData.concat(res.data);
        addLog(`已解析 ${file.name}: 发现 ${res.data.length} 行数据`, 'info');
    }

    dataHeaders.value = Array.from(headers);
    mergedData.value = allData;
    
    // Auto Map
    autoMapFields();
    step.value = 3;
    addLog(`准备就绪: 共载入 ${allData.length} 行数据`, 'info');

  } catch (e: any) {
    ElMessage.error(e.message);
    addLog(e.message, 'error');
  } finally {
    isProcessing.value = false;
  }
};

const autoMapFields = () => {
    // 1. Map Columns
    templateColumns.value.forEach(col => {
        if (isDimensionCol(col.name)) {
            mapping[col.name + '_L'] = dataHeaders.value.find(h => h.includes('长') || h.toLowerCase().includes('length')) || '';
            mapping[col.name + '_W'] = dataHeaders.value.find(h => h.includes('宽') || h.toLowerCase().includes('width')) || '';
            mapping[col.name + '_H'] = dataHeaders.value.find(h => h.includes('高') || h.toLowerCase().includes('height')) || '';
        } else {
            const match = dataHeaders.value.find(h => h.includes(col.name) || col.name.includes(h));
            if (match) mapping[col.name] = match;
        }
    });

    // 2. Map Config
    const findHeader = (keywords: string[]) => dataHeaders.value.find(h => keywords.some(k => h.includes(k)));
    
    const groupCol = findHeader(['仓库', 'Warehouse', 'FBA']);
    if (groupCol) config.groupBy = groupCol;

    const sumCol = findHeader(['箱数', 'CTN', 'Qty', '数量']);
    if (sumCol) config.sumBy = sumCol;
};

const processAndDownload = async () => {
    if (!config.groupBy) {
        ElMessage.warning('请选择一个分仓依据列');
        return;
    }
    if (!templateFile.value) return;

    isProcessing.value = true;
    addLog('正在生成文件...', 'info');

    try {
        const blob = await Generator.generateZip(
            mergedData.value,
            templateFile.value,
            mapping,
            templateColumns.value,
            config,
            warehouseMap.value
        );

        saveAs(blob, `FBA下单表_${new Date().toISOString().slice(0,10)}.zip`);
        addLog('下载已开始!', 'info');
        ElMessage.success('下载已开始');
    } catch (e: any) {
        console.error(e);
        ElMessage.error('生成失败');
        addLog(e.message, 'error');
    } finally {
        isProcessing.value = false;
    }
};

const reset = () => {
    step.value = 1;
    templateFile.value = null;
    templateColumns.value = [];
    mergedData.value = [];
    dataHeaders.value = [];
    logs.value = [];
    addLog('系统已重置', 'info');
};

const isImageCol = (name: string) => name.includes('图片') || name.includes('Photo') || name.includes('Image');

</script>

<template>
  <div class="app-container">
    <!-- Header -->
    <div class="header">
        <h1>FBA 智能下单表工具 <el-tag type="warning" size="small">专业版 Beta</el-tag></h1>
        <div style="display: flex; gap: 10px;">
            <el-upload
                action="#"
                :auto-upload="false"
                :show-file-list="false"
                accept=".json"
                :on-change="(file: any) => handleConfigImport(file.raw)"
            >
                <el-button icon="Download" round size="small">导入配置</el-button>
            </el-upload>
            <el-button icon="Upload" round size="small" @click="exportConfig">导出配置</el-button>
            <el-button @click="reset" icon="RefreshLeft" circle title="重置" />
        </div>
    </div>

    <!-- Steps -->
    <div class="steps-box">
        <el-steps :active="step - 1" finish-status="success" align-center>
            <el-step title="上传模板" description="选择空白模板.xlsx" />
            <el-step title="上传数据源" description="含产品图的表" />
            <el-step title="生成下载" description="自动分仓打包" />
        </el-steps>
    </div>

    <!-- Step 1: Template -->
    <div v-if="step === 1" class="step-content upload-container">
         <el-upload
            class="upload-demo"
            drag
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            accept=".xlsx"
            :on-change="(file: any) => handleTemplateUpload(file.raw)"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将模板拖到此处，或<em>点击上传</em>
            </div>
          </el-upload>
    </div>

    <!-- Step 2: Data -->
    <div v-if="step === 2" class="step-content upload-container">
         <el-alert :title="`当前模板: ${templateFile?.name}`" type="success" show-icon :closable="false" style="margin-bottom:20px;" />
         
         <el-upload
            class="upload-demo"
            drag
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            multiple
            accept=".xlsx"
            :on-change="(_file: any, fileList: any) => handleDataUpload(fileList.map((f:any) => f.raw))"
          >
            <el-icon class="el-icon--upload"><picture /></el-icon>
            <div class="el-upload__text">
              上传数据源文件 (支持多选)
            </div>
          </el-upload>
    </div>

    <!-- Step 3: Config -->
    <div v-if="step === 3" class="step-content config-container">
        <!-- Settings -->
        <div class="config-left">
            <el-card header="核心配置">
                <el-form label-position="top">
                    <el-row :gutter="20">
                        <el-col :span="12">
                            <el-form-item label="分仓依据 (Grouper)">
                                <el-select v-model="config.groupBy" filterable placeholder="选择仓库列">
                                    <el-option v-for="h in dataHeaders" :key="h" :label="h" :value="h" />
                                </el-select>
                            </el-form-item>
                        </el-col>
                         <el-col :span="12">
                            <el-form-item label="箱数统计 (Sum)">
                                <el-select v-model="config.sumBy" filterable placeholder="选择箱数列">
                                    <el-option v-for="h in dataHeaders" :key="h" :label="h" :value="h" />
                                </el-select>
                            </el-form-item>
                        </el-col>
                    </el-row>
                    <el-form-item label="报关方式 (B9)">
                        <el-radio-group v-model="config.declareType">
                            <el-radio-button label="单独报关件" />
                            <el-radio-button label="非报关件" />
                            <el-radio-button label="合并报关件" />
                        </el-radio-group>
                    </el-form-item>
                </el-form>
            </el-card>

            <el-card header="字段映射" style="margin-top: 20px;">
                <div class="mapping-list">
                    <div v-for="col in templateColumns" :key="col.index" class="mapping-item">
                        <div class="mapping-label">
                            <strong>{{ col.name }}</strong>
                            <el-tag v-if="isImageCol(col.name)" size="small" type="success">含图片</el-tag>
                        </div>
                        <div v-if="isDimensionCol(col.name)" class="dimension-mapping">
                            <div class="dim-row">
                                <span>长:</span>
                                <el-select v-model="mapping[col.name + '_L']" clearable filterable size="small" placeholder="长">
                                    <el-option v-for="h in dataHeaders" :key="h" :label="h" :value="h" />
                                </el-select>
                            </div>
                            <div class="dim-row">
                                <span>宽:</span>
                                <el-select v-model="mapping[col.name + '_W']" clearable filterable size="small" placeholder="宽">
                                    <el-option v-for="h in dataHeaders" :key="h" :label="h" :value="h" />
                                </el-select>
                            </div>
                            <div class="dim-row">
                                <span>高:</span>
                                <el-select v-model="mapping[col.name + '_H']" clearable filterable size="small" placeholder="高">
                                    <el-option v-for="h in dataHeaders" :key="h" :label="h" :value="h" />
                                </el-select>
                            </div>
                        </div>
                        <el-select v-else v-model="mapping[col.name]" clearable filterable size="small" placeholder="请选择数据列">
                             <el-option v-for="h in dataHeaders" :key="h" :label="h" :value="h" />
                        </el-select>
                    </div>
                </div>
            </el-card>
        </div>

        <!-- Actions -->
        <div class="config-right">
             <el-button type="primary" size="large" :loading="isProcessing" @click="processAndDownload" style="width: 100%; height: 60px; font-size: 18px;">
                {{ isProcessing ? '正在处理图片...' : '生成并下载 ZIP' }}
             </el-button>

             <div class="log-box">
                <div v-for="(log, i) in logs" :key="i" :class="['log-item', log.type]">
                    [{{ log.time }}] {{ log.msg }}
                </div>
             </div>
        </div>
    </div>

  </div>
</template>

<style>
body { margin: 0; background: #f0f2f5; font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif; }
.app-container { max-width: 1200px; margin: 20px auto; background: #fff; min-height: 90vh; border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1); overflow: hidden; }
.header { background: #409EFF; color: #fff; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; }
.header h1 { margin: 0; font-size: 22px; }
.steps-box { padding: 30px; background: #fafafa; border-bottom: 1px solid #ebeef5; }
.step-content { padding: 30px; }
.upload-container { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; }
.upload-demo { width: 100%; max-width: 500px; }
.config-container { display: flex; gap: 30px; align-items: flex-start; }
.config-left { flex: 2; }
.config-right { flex: 1; position: sticky; top: 20px;}

.mapping-list { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; max-height: 500px; overflow-y: auto; }
.mapping-item { background: #f9f9f9; padding: 10px; border-radius: 4px; border: 1px solid #eee; }
.mapping-label { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 13px; }

.log-box { background: #1e1e1e; color: #67c23a; padding: 15px; font-family: monospace; height: 400px; overflow-y: auto; margin-top: 20px; border-radius: 6px; font-size: 12px; }
.log-item { margin-bottom: 4px; }
.log-item.error { color: #f56c6c; }
.log-item.warn { color: #e6a23c; }

.dimension-mapping { display: flex; flex-direction: column; gap: 4px; padding-top: 5px; }
.dim-row { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.dim-row span { width: 30px; color: #909399; }
</style>
