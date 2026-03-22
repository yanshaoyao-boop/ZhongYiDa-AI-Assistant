<script setup lang="ts">
import { ref } from 'vue';
import { Upload, FileSpreadsheet, Archive, CheckCircle2 } from 'lucide-vue-next';

const emit = defineEmits<{
  (e: 'files-picked', files: File[]): void;
}>();

const isOver = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

const onDrop = (e: DragEvent) => {
  isOver.value = false;
  const files = Array.from(e.dataTransfer?.files || []);
  if (files.length > 0) {
    emit('files-picked', files);
  }
};

const onFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement;
  const files = Array.from(target.files || []);
  if (files.length > 0) {
    emit('files-picked', files);
    target.value = ''; // Reset
  }
};

const triggerFileInput = () => {
  fileInput.value?.click();
};
</script>

<template>
  <div 
    class="relative group"
    @dragover.prevent="isOver = true"
    @dragleave.prevent="isOver = false"
    @drop.prevent="onDrop"
  >
    <div 
      :class="[
        'glass-card p-12 flex flex-col items-center justify-center border-2 border-dashed transition-all duration-300 cursor-pointer',
        isOver ? 'border-brand-500 bg-brand-5 scale-[1.01]' : 'border-slate-200 hover:border-brand-300 hover:bg-slate-50'
      ]"
      @click="triggerFileInput"
    >
      <input 
        type="file" 
        ref="fileInput" 
        class="hidden" 
        multiple 
        accept=".xlsx,.xls,.zip"
        @change="onFileChange"
      >
      
      <div :class="[
        'w-20 h-20 rounded-2xl flex items-center justify-center mb-6 transition-all duration-500',
        isOver ? 'bg-brand-500 text-white rotate-6 scale-110 shadow-lg shadow-brand-200' : 'bg-slate-100 text-slate-400 group-hover:text-brand-500 group-hover:bg-brand-50'
      ]">
        <Upload class="w-10 h-10" />
      </div>

      <h2 class="text-xl font-semibold text-slate-800 mb-2">
        {{ isOver ? '放下文件开始解析' : '拖拽文件到这里' }}
      </h2>
      <p class="text-slate-500 text-sm text-center max-w-xs">
        支持 <span class="text-brand-600 font-medium">Excel (.xlsx, .xls)</span> 和 <span class="text-brand-600 font-medium">ZIP</span> 压缩包。
        系统将自动提取其中的下单表并按仓库分组。
      </p>

      <div class="mt-8 flex gap-4">
        <div class="flex items-center gap-1.5 text-[11px] text-slate-600 bg-white px-3 py-1 rounded-full border border-slate-200 shadow-sm">
          <FileSpreadsheet class="w-3.5 h-3.5 text-emerald-500" /> Spreadsheet Ready
        </div>
        <div class="flex items-center gap-1.5 text-[11px] text-slate-600 bg-white px-3 py-1 rounded-full border border-slate-200 shadow-sm">
          <Archive class="w-3.5 h-3.5 text-amber-500" /> ZIP Support
        </div>
        <div class="flex items-center gap-1.5 text-[11px] text-slate-600 bg-white px-3 py-1 rounded-full border border-slate-200 shadow-sm">
          <CheckCircle2 class="w-3.5 h-3.5 text-brand-500" /> High Precision
        </div>
      </div>
    </div>
  </div>
</template>
