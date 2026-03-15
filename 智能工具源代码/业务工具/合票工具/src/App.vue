<script setup lang="ts">
import { ref, reactive } from 'vue';
import { Layers, ListChecks, Info, RefreshCcw, Github } from 'lucide-vue-next';
import ExcelJS from 'exceljs';
import FileUploader from './components/FileUploader.vue';
import GroupCard from './components/GroupCard.vue';
import ConsoleLog from './components/ConsoleLog.vue';
import { ExcelHandler, type FileMetadata, type ProcessingLog } from './utils/excel-handler';
import { ZipHandler } from './utils/zip-handler';

const groups = reactive<Record<string, FileMetadata[]>>({});
const totalFileCount = ref(0);
const logs = ref<ProcessingLog[]>([]);
const isProcessing = ref(false);
const mergingCodes = ref<Set<string>>(new Set());

const addLog = (msg: string, type: ProcessingLog['type'] = 'info') => {
  logs.value.push({
    time: new Date().toLocaleTimeString(),
    msg,
    type
  });
};

const handleFilesPicked = async (files: File[]) => {
  isProcessing.value = true;
  addLog(`选择了 ${files.length} 个文件，开始解析...`, 'info');

  try {
    for (const file of files) {
      if (file.name.toLowerCase().endsWith('.zip')) {
        addLog(`正在解压: ${file.name}`, 'info');
        const unzipped = await ZipHandler.unzip(file);
        addLog(`从 ZIP 中解压出 ${unzipped.length} 个 Excel 文件`, 'success');
        await processBuffers(unzipped);
      } else {
        const buffer = await file.arrayBuffer();
        await processBuffers([{ name: file.name, buffer }]);
      }
    }
  } catch (error: any) {
    addLog(`解析出错: ${error.message}`, 'error');
  } finally {
    isProcessing.value = false;
  }
};

const processBuffers = async (items: { name: string; buffer: ArrayBuffer }[]) => {
  for (const item of items) {
    try {
      const workbook = new ExcelJS.Workbook();
      await workbook.xlsx.load(item.buffer);
      const sheet = workbook.worksheets[0];
      
      const { warehouseCode, headerRow } = ExcelHandler.analyzeSheet(sheet);
      
      const metadata: FileMetadata = {
        name: item.name,
        buffer: item.buffer,
        warehouseCode,
        headerRow
      };

      if (!groups[warehouseCode]) {
        groups[warehouseCode] = [];
      }
      
      const existing = groups[warehouseCode].find(f => f.name === item.name);
      if (!existing) {
        groups[warehouseCode].push(metadata);
        totalFileCount.value++;
      }
    } catch (e: any) {
      addLog(`无法解析文件 ${item.name}: ${e.message}`, 'error');
    }
  }
};

const handleMerge = async (code: string) => {
  if (mergingCodes.value.has(code)) return;
  
  mergingCodes.value.add(code);
  await ExcelHandler.mergeGroup(code, groups[code], (log) => {
    logs.value.push(log);
  });
  mergingCodes.value.delete(code);
};

const resetAll = () => {
  Object.keys(groups).forEach(key => delete groups[key]);
  totalFileCount.value = 0;
  logs.value = [];
  addLog('已重置所有数据', 'warn');
};
</script>

<template>
  <div class="min-h-screen bg-[#f8fafc] text-slate-900 selection:bg-brand-500 selection:text-white">
    <!-- Subtle background pattern -->
    <div class="fixed inset-0 overflow-hidden -z-10 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:24px_24px] [mask-image:radial-gradient(ellipse_50%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>

    <header class="border-b border-slate-200 bg-white/80 backdrop-blur-md sticky top-0 z-50 shadow-sm">
      <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 bg-gradient-to-tr from-brand-600 to-indigo-500 rounded-lg flex items-center justify-center shadow-lg shadow-brand-500/20">
            <Layers class="text-white w-5 h-5" />
          </div>
          <h1 class="text-lg font-bold text-slate-800">
            FBA 合票神器 <span class="text-xs font-normal text-slate-400 ml-1">Pro v2.0</span>
          </h1>
        </div>

        <div class="flex items-center gap-6">
          <div v-if="totalFileCount > 0" class="flex items-center gap-2 bg-emerald-50 text-emerald-600 px-3 py-1 rounded-full text-xs font-bold border border-emerald-100">
            <ListChecks class="w-3.5 h-3.5" /> 已加载 {{ totalFileCount }} 个文件
          </div>
          <button 
            @click="resetAll"
            class="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all"
            title="清空记录"
          >
            <RefreshCcw class="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-10">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <!-- Left Column: Upload & Log -->
        <div class="lg:col-span-1 space-y-6">
          <section>
            <div class="flex items-center gap-2 mb-4">
              <span class="w-1.5 h-1.5 bg-brand-500 rounded-full"></span>
              <h2 class="text-sm font-bold uppercase tracking-widest text-slate-500">资源上传</h2>
            </div>
            <FileUploader @files-picked="handleFilesPicked" />
          </section>

          <section>
            <ConsoleLog :logs="logs" />
          </section>

          <div class="glass-card p-5 bg-gradient-to-br from-brand-50 to-transparent border-brand-100">
            <div class="flex gap-4">
              <Info class="w-5 h-5 text-brand-500 shrink-0" />
              <div>
                <h4 class="text-sm font-bold text-slate-700 mb-1">使用说明</h4>
                <p class="text-xs text-slate-500 leading-relaxed">
                  请上传标准的 FBA 下单表。本工具将自动识别仓库代码并归类。合并时会保留原表的单元格样式、公式和图片。
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: Results -->
        <div class="lg:col-span-2">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <span class="w-1.5 h-1.5 bg-brand-500 rounded-full"></span>
              <h2 class="text-sm font-bold uppercase tracking-widest text-slate-500">仓库分组识别</h2>
            </div>
            
            <div v-if="Object.keys(groups).length > 0" class="text-xs text-slate-400">
              共识别出 {{ Object.keys(groups).length }} 个仓库代码
            </div>
          </div>

          <div v-if="Object.keys(groups).length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-for="(files, code) in groups" :key="code">
              <GroupCard 
                :code="code" 
                :files="files" 
                :is-merging="mergingCodes.has(code)"
                @merge="handleMerge"
              />
            </div>
          </div>

          <div v-else class="glass-card h-96 flex flex-col items-center justify-center border-dashed border-2 border-slate-200 bg-white/50">
            <div class="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center text-slate-300 mb-4">
              <Layers class="w-8 h-8" />
            </div>
            <p class="text-slate-400 text-sm italic text-center">
              暂无识别数据<br>
              <span class="text-xs">请先在左侧上传文件</span>
            </p>
          </div>
        </div>

      </div>
    </main>

    <footer class="mt-20 py-10 border-t border-slate-200">
      <div class="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
        <p class="text-xs text-slate-400">
          © 2024 Dev-Forge. 精诚合票工具 - 专为跨境电商优化
        </p>
        <div class="flex items-center gap-6">
          <a href="#" class="text-slate-300 hover:text-slate-600 transition-colors"><Github class="w-4 h-4" /></a>
          <span class="text-[10px] text-slate-300 font-mono">STABLE_RELEASE_V2</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<style>
/* Global scrollbar for the app */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.1);
}
</style>
