<script setup lang="ts">
import { ref, computed } from 'vue';
import { Plus, Play, RefreshCw, Settings2, Info } from 'lucide-vue-next';
import { ElMessage, ElLoading } from 'element-plus';
import * as XLSX from 'xlsx-js-style';
import FileUploader from './components/FileUploader.vue';
import ReconciliationResultComp from './components/ReconciliationResult.vue';
import type { FileData, ReconciliationResult } from './logic/excelProcessor';
import { runReconciliation } from './logic/excelProcessor';

const salesFile = ref<FileData>({
  id: 'sales',
  status: 'idle',
  data: [],
  headers: [],
  name: '',
  headerIdx: 0,
  idCol: '',
  amtCol: ''
});

const agentFiles = ref<FileData[]>([
  { id: Date.now(), status: 'idle', data: [], headers: [], name: '', headerIdx: 0, idCol: '', amtCol: '' }
]);

const targetSalesperson = ref('ALL');
const tolerance = ref(0.05);
const result = ref<ReconciliationResult | null>(null);

const addAgentFile = () => {
  agentFiles.value.push({
    id: Date.now(),
    status: 'idle',
    data: [],
    headers: [],
    name: '',
    headerIdx: 0,
    idCol: '',
    amtCol: ''
  });
};

const removeAgentFile = (index: number) => {
  agentFiles.value.splice(index, 1);
};

const availableSalespeople = computed(() => {
  const set = new Set<string>();
  agentFiles.value.forEach(f => {
    if (f.status === 'loaded' && f.salespersonCol) {
      const idx = f.headers.indexOf(f.salespersonCol);
      if (idx > -1) {
        f.data.forEach(row => {
          if (row[idx]) set.add(String(row[idx]).trim());
        });
      }
    }
  });
  return Array.from(set).sort();
});

const isReady = computed(() => {
  return salesFile.value.status === 'loaded' && agentFiles.value.some(f => f.status === 'loaded');
});

const handleReconcile = () => {
  const loading = ElLoading.service({ text: '深度数据分析中...', background: 'rgba(255, 255, 255, 0.8)' });
  setTimeout(() => {
    try {
      result.value = runReconciliation(
        salesFile.value,
        agentFiles.value,
        targetSalesperson.value,
        tolerance.value
      );
      ElMessage.success(result.value.isMatch ? '对账圆满成功！' : '发现数据差异，请核查');
    } catch (err) {
      ElMessage.error('计算出错，请检查文件格式');
    } finally {
      loading.close();
    }
  }, 600);
};

const exportDiff = () => {
  if (!result.value) return;
  const data = result.value.discrepancies.map(d => ({
    '单号/编号': d.id,
    '客户': d.client,
    '业务员汇总金额': d.sumSales,
    '业务员记录笔数': d.countSales,
    '代理汇总金额': d.sumAgent,
    '偏差金额': d.diff
  }));
  const ws = XLSX.utils.json_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "对账异常报告");
  XLSX.writeFile(wb, `差异报告_${new Date().toLocaleDateString()}.xlsx`);
};

const exportAnnotated = async () => {
  if (!salesFile.value.rawFile || !result.value) return;
  
  const loading = ElLoading.service({ text: '正在渲染 Excel 样式...' });
  try {
    const reader = new FileReader();
    reader.onload = (e) => {
      const data = new Uint8Array(e.target?.result as ArrayBuffer);
      const wb = XLSX.read(data, { type: 'array', cellStyles: true });
      const ws = wb.Sheets[salesFile.value.currentSheet!];
      
      const range = XLSX.utils.decode_range(ws['!ref']!);
      const lastCol = range.e.c;
      
      // Build lookup for fast styling
      const diffMap = new Map(result.value!.discrepancies.map(d => [d.id, d]));
      const sIdIdx = salesFile.value.headers.indexOf(salesFile.value.idCol);

      // Headers
      ["对账结果", "差额详细"].forEach((h, i) => {
        const ref = XLSX.utils.encode_cell({ r: salesFile.value.headerIdx, c: lastCol + 1 + i });
        ws[ref] = { v: h, s: { font: { bold: true, color: { rgb: "FFFFFF" } }, fill: { fgColor: { rgb: "2563EB" } } } };
      });

      // Data Rows
      salesFile.value.data.forEach((row, idx) => {
        const rIdx = salesFile.value.headerIdx + 1 + idx;
        const id = String(row[sIdIdx] || '').trim();
        const diff = diffMap.get(id);
        
        const cellStatus = XLSX.utils.encode_cell({ r: rIdx, c: lastCol + 1 });
        const cellInfo = XLSX.utils.encode_cell({ r: rIdx, c: lastCol + 2 });

        if (diff) {
          ws[cellStatus] = { v: "❌ 差异", s: { fill: { fgColor: { rgb: "FEE2E2" } }, font: { color: { rgb: "B91C1C" } } } };
          ws[cellInfo] = { v: diff.diff, t: 'n' };
        } else if (id) {
          ws[cellStatus] = { v: "✅ 匹配", s: { fill: { fgColor: { rgb: "DCFCE7" } }, font: { color: { rgb: "15803D" } } } };
        }
      });

      range.e.c = lastCol + 2;
      ws['!ref'] = XLSX.utils.encode_range(range);
      XLSX.writeFile(wb, `核对报告_${salesFile.value.name}`);
      loading.close();
    };
    reader.readAsArrayBuffer(salesFile.value.rawFile);
  } catch (err) {
    loading.close();
    ElMessage.error('导出失败');
  }
};
const resetApp = () => {
  window.location.reload();
};
</script>

<template>
  <div class="min-h-screen bg-[#f8fafc] pb-20">
    <!-- Navbar -->
    <header class="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur-md">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-600 text-white shadow-lg shadow-primary-200">
            <RefreshCw :size="20" />
          </div>
          <div>
            <h1 class="text-lg font-bold tracking-tight text-slate-900">自动对账助手 Pro</h1>
            <p class="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">Reconciliation Engine v2.0</p>
          </div>
        </div>
        
        <div class="flex items-center gap-4">
          <button @click="resetApp" class="text-sm font-medium text-slate-500 hover:text-slate-800">重置工作区</button>
          <div class="h-4 w-px bg-slate-200"></div>
          <a href="#" class="flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800">
            <Info :size="16" />
            使用指南
          </a>
        </div>
      </div>
    </header>

    <main class="mx-auto mt-10 max-w-7xl px-6">
      <div class="grid grid-cols-1 gap-10 lg:grid-cols-12">
        <!-- Left Column: Source Data -->
        <div class="lg:col-span-4">
          <div class="mb-5 flex items-center gap-2">
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-primary-600 text-[10px] font-bold text-white">01</span>
            <h2 class="text-sm font-bold uppercase tracking-widest text-slate-400">业务员原始数据</h2>
          </div>
          <FileUploader v-model="salesFile" title="业务员自填数据" theme="blue" enable-client-selection />
          
          <div class="mt-8">
            <div class="rounded-2xl border border-blue-100 bg-blue-50/50 p-5">
              <div class="mb-3 flex items-center gap-2 text-blue-700">
                <Settings2 :size="18" />
                <span class="text-sm font-bold">自动化策略</span>
              </div>
              <p class="text-xs leading-relaxed text-blue-600/80">
                系统将自动对同一编号的多条记录进行求和，并支持按照业务员筛选特定范围进行比对。
              </p>
            </div>
          </div>
        </div>

        <!-- Right Column: Benchmarks -->
        <div class="lg:col-span-8">
          <div class="mb-5 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-600 text-[10px] font-bold text-white">02</span>
              <h2 class="text-sm font-bold uppercase tracking-widest text-slate-400">代理结算基准数据</h2>
            </div>
            <button 
              @click="addAgentFile"
              class="flex items-center gap-1.5 text-xs font-bold text-emerald-600 hover:text-emerald-700"
            >
              <Plus :size="14" />
              添加代理文件
            </button>
          </div>

          <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div v-for="(file, idx) in agentFiles" :key="file.id">
              <FileUploader 
                v-model="agentFiles[idx]" 
                :title="`代理数据 #${idx + 1}`" 
                theme="emerald" 
                compact 
                :show-remove="agentFiles.length > 1"
                @remove="removeAgentFile(idx)"
                enable-salesperson-selection
              />
            </div>
          </div>

          <!-- Final Actions -->
          <transition name="el-fade-in">
            <div v-if="isReady" class="mt-12 rounded-3xl bg-slate-900 p-8 shadow-2xl shadow-slate-200">
              <div class="flex flex-col items-center justify-between gap-6 md:flex-row">
                <div class="flex gap-8">
                  <div class="flex flex-col gap-1.5">
                    <label class="text-[10px] font-bold uppercase tracking-widest text-slate-500">核对业务员</label>
                    <el-select v-model="targetSalesperson" size="default" class="!w-48 dark-select">
                      <el-option label="全部 (合并)" value="ALL" />
                      <el-option v-for="sp in availableSalespeople" :key="sp" :label="sp" :value="sp" />
                    </el-select>
                  </div>
                  <div class="flex flex-col gap-1.5">
                    <label class="text-[10px] font-bold uppercase tracking-widest text-slate-500">容差 (±)</label>
                    <el-input-number v-model="tolerance" :precision="2" :step="0.01" :min="0" size="default" class="!w-32 dark-number" />
                  </div>
                </div>
                
                <button 
                  @click="handleReconcile"
                  class="group flex items-center gap-3 rounded-2xl bg-white px-8 py-4 font-bold text-slate-900 transition-all hover:bg-primary-50 active:scale-95"
                >
                  <Play :size="20" class="fill-current" />
                  执行深度核对
                </button>
              </div>
            </div>
          </transition>

          <!-- Result Display -->
          <ReconciliationResultComp 
            v-if="result" 
            :result="result" 
            @export-diff="exportDiff"
            @export-annotated="exportAnnotated"
          />
        </div>
      </div>
    </main>

    <footer class="mt-32 border-t border-slate-200 pt-10 text-center">
      <p class="text-sm font-medium text-slate-400">仲易达集团 · 数字化财务管理系统</p>
      <div class="mt-4 flex justify-center gap-6">
        <div class="h-2 w-2 rounded-full bg-emerald-500"></div>
        <div class="h-2 w-2 rounded-full bg-primary-500"></div>
        <div class="h-2 w-2 rounded-full bg-amber-500"></div>
      </div>
    </footer>
  </div>
</template>

<style>
/* Custom Select/Input Styling for Dark Panel */
.dark-select :deep(.el-input__wrapper) {
  background-color: #1e293b !important;
  box-shadow: 0 0 0 1px #334155 inset !important;
}
.dark-select :deep(.el-input__inner) {
  color: white !important;
}
.dark-number :deep(.el-input__wrapper) {
  background-color: #1e293b !important;
  box-shadow: 0 0 0 1px #334155 inset !important;
}
.dark-number :deep(.el-input__inner) {
  color: white !important;
}
.dark-number :deep(.el-input-number__decrease),
.dark-number :deep(.el-input-number__increase) {
  background-color: #0f172a !important;
  border-color: #334155 !important;
  color: #94a3b8 !important;
}

/* Animations */
.animate-in {
  animation-duration: 0.5s;
  animation-fill-mode: both;
}
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes slide-in-from-bottom-5 {
  from { transform: translateY(1.25rem); }
  to { transform: translateY(0); }
}
.fade-in { animation-name: fade-in; }
.slide-in-from-bottom-5 { animation-name: slide-in-from-bottom-5; }
</style>
