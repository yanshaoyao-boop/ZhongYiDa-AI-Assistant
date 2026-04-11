<script setup lang="ts">
import { computed } from 'vue';
import { UploadCloud, FileText, CheckCircle2, X, Trash2 } from 'lucide-vue-next';
import type { FileData } from '../logic/excelProcessor';
import { processExcelFile } from '../logic/excelProcessor';

interface Props {
  modelValue: FileData;
  title: string;
  theme?: 'blue' | 'emerald';
  compact?: boolean;
  showRemove?: boolean;
  enableClientSelection?: boolean;
  enableSalespersonSelection?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  theme: 'blue',
  compact: false,
  showRemove: false,
});

const emit = defineEmits(['update:modelValue', 'remove']);

const handleFileSelect = async (file: any) => {
  const result = await processExcelFile(file.raw);
  emit('update:modelValue', { ...props.modelValue, ...result });
};

const handleSheetChange = async (sheetName: string) => {
  if (!props.modelValue.rawFile) return;
  const result = await processExcelFile(props.modelValue.rawFile, sheetName);
  emit('update:modelValue', { ...props.modelValue, ...result });
};

const clearFile = () => {
  emit('update:modelValue', {
    id: props.modelValue.id,
    status: 'idle',
    data: [],
    headers: [],
    sheets: [],
    name: '',
    headerIdx: 0,
    idCol: '',
    amtCol: '',
    currentSheet: '',
    rawFile: undefined
  });
};

const themeClasses = computed(() => {
  if (props.theme === 'emerald') return 'border-emerald-500 bg-emerald-50/30';
  return 'border-primary-600 bg-primary-50/30';
});
</script>

<template>
  <div 
    class="relative overflow-hidden rounded-2xl border bg-white p-5 transition-all duration-300 hover:shadow-lg"
    :class="[themeClasses, modelValue.status === 'loaded' ? 'shadow-md' : 'shadow-sm']"
  >
    <!-- Header -->
    <div class="mb-4 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <div 
          class="flex h-8 w-8 items-center justify-center rounded-lg"
          :class="theme === 'emerald' ? 'bg-emerald-100 text-emerald-600' : 'bg-primary-100 text-primary-600'"
        >
          <component :is="modelValue.status === 'loaded' ? CheckCircle2 : FileText" :size="18" />
        </div>
        <h3 class="font-semibold text-slate-800">{{ title }}</h3>
      </div>
      
      <button 
        v-if="modelValue.status === 'loaded'"
        @click="clearFile"
        class="rounded-full p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
      >
        <Trash2 :size="16" />
      </button>
      <button 
        v-else-if="showRemove"
        @click="$emit('remove')"
        class="rounded-full p-1.5 text-slate-400 transition-colors hover:bg-slate-100"
      >
        <X :size="16" />
      </button>
    </div>

    <!-- Upload Area -->
    <div v-if="modelValue.status === 'idle'" class="group relative">
      <el-upload
        class="w-full"
        drag
        action="#"
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFileSelect"
        accept=".xlsx, .xls"
      >
        <div class="flex flex-col items-center justify-center py-4">
          <div class="mb-3 rounded-full bg-slate-50 p-4 transition-transform duration-300 group-hover:scale-110">
            <UploadCloud :size="32" class="text-primary-500" />
          </div>
          <p class="text-sm font-medium text-slate-600">点击或拖拽上传表格</p>
          <p class="mt-1 text-xs text-slate-400">支持 Excel (.xlsx, .xls)</p>
        </div>
      </el-upload>
    </div>

    <!-- Loaded State -->
    <div v-else class="space-y-4">
      <div class="flex items-center gap-3 rounded-xl bg-slate-50 p-3">
        <div class="rounded-lg bg-white p-2 shadow-sm">
          <FileText :size="20" class="text-slate-500" />
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-semibold text-slate-700">{{ modelValue.name }}</p>
          <p class="text-xs text-slate-400">{{ modelValue.data.length }} 行记录</p>
        </div>
      </div>

      <!-- Config Grid -->
      <div class="grid grid-cols-2 gap-3">
        <div v-if="(modelValue.sheets || []).length > 1" class="col-span-2 space-y-1.5">
          <label class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Sheet</label>
          <el-select
            :model-value="modelValue.currentSheet"
            size="small"
            class="w-full"
            @change="handleSheetChange"
          >
            <el-option v-for="sheet in modelValue.sheets" :key="sheet" :label="sheet" :value="sheet" />
          </el-select>
        </div>
        <div class="space-y-1.5">
          <label class="text-[11px] font-bold uppercase tracking-wider text-slate-400">单号/编号列</label>
          <el-select v-model="modelValue.idCol" size="small" class="w-full">
            <el-option v-for="(h, idx) in modelValue.headers" :key="`${idx}-${h}`" :label="h" :value="h" />
          </el-select>
        </div>
        <div class="space-y-1.5">
          <label class="text-[11px] font-bold uppercase tracking-wider text-slate-400">金额列</label>
          <el-select v-model="modelValue.amtCol" size="small" class="w-full">
            <el-option v-for="(h, idx) in modelValue.headers" :key="`${idx}-${h}`" :label="h" :value="h" />
          </el-select>
        </div>
        
        <div v-if="enableClientSelection" class="col-span-2 space-y-1.5">
          <label class="text-[11px] font-bold uppercase tracking-wider text-slate-400">客户/来源列</label>
          <el-select v-model="modelValue.clientCol" size="small" class="w-full" clearable placeholder="可选：自动匹配客户">
            <el-option v-for="(h, idx) in modelValue.headers" :key="`${idx}-${h}`" :label="h" :value="h" />
          </el-select>
        </div>

        <div v-if="enableSalespersonSelection" class="col-span-2 space-y-1.5">
          <label class="text-[11px] font-bold uppercase tracking-wider text-slate-400">业务员筛选列</label>
          <el-select v-model="modelValue.salespersonCol" size="small" class="w-full" clearable placeholder="可选：用于按业务员对账">
            <el-option v-for="(h, idx) in modelValue.headers" :key="`${idx}-${h}`" :label="h" :value="h" />
          </el-select>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(.el-upload-dragger) {
  border-width: 2px !important;
  border-style: dashed !important;
  background-color: transparent !important;
  border-color: #e2e8f0 !important;
  border-radius: 1rem !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

:deep(.el-upload-dragger:hover) {
  border-color: #3b82f6 !important;
  background-color: #f8fafc !important;
}
</style>
