<script setup lang="ts">
import { ref } from 'vue';
import { Package, Download, Files, Loader2, ChevronRight } from 'lucide-vue-next';
import type { FileMetadata } from '../utils/excel-handler';

const props = defineProps<{
  code: string;
  files: FileMetadata[];
  isMerging: boolean;
}>();

const emit = defineEmits<{
  (e: 'merge', code: string): void;
}>();

const showAll = ref(false);
</script>

<template>
  <div class="glass-card overflow-hidden group/card hover:ring-2 hover:ring-brand-500/20 transition-all flex flex-col h-full border-slate-200">
    <div class="p-5 flex items-start justify-between border-b border-slate-100 bg-slate-50/50">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center text-brand-500 group-hover/card:bg-brand-500 group-hover/card:text-white transition-all">
          <Package class="w-5 h-5" />
        </div>
        <div>
          <h3 class="text-lg font-bold text-slate-800 leading-tight">{{ code }}</h3>
          <p class="text-xs text-slate-500 font-medium">FBA 仓库分组</p>
        </div>
      </div>
      <div class="bg-slate-100 text-slate-600 text-[11px] font-bold px-2 py-0.5 rounded border border-slate-200">
        {{ files.length }} FILES
      </div>
    </div>

    <div class="flex-1 p-5">
      <ul class="space-y-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
        <li 
          v-for="(file, idx) in (showAll ? files : files.slice(0, 5))" 
          :key="idx"
          class="flex items-center gap-2 text-xs text-slate-600 py-1 border-b border-slate-50 last:border-0"
        >
          <Files class="w-3 h-3 shrink-0 text-slate-400" />
          <span class="truncate" :title="file.name">{{ file.name }}</span>
        </li>
      </ul>
      <button 
        v-if="files.length > 5"
        @click="showAll = !showAll"
        class="mt-2 text-[10px] font-bold text-slate-400 hover:text-brand-600 flex items-center gap-1 transition-colors"
      >
        {{ showAll ? '收起' : `查看全部 ${files.length} 个文件` }}
        <ChevronRight :class="['w-3 h-3 transition-transform', showAll ? '-rotate-90' : 'rotate-90']" />
      </button>

      <div v-if="files.length === 0" class="h-24 flex items-center justify-center text-slate-400 italic text-sm">
        暂无文件
      </div>
    </div>

    <div class="p-5 pt-0 mt-auto">
      <button 
        @click="emit('merge', code)"
        :disabled="isMerging"
        class="w-full bg-brand-600 hover:bg-brand-500 shadow-lg shadow-brand-100 disabled:bg-slate-100 disabled:text-slate-400 disabled:shadow-none text-white font-semibold py-2.5 rounded-xl flex items-center justify-center gap-2 transition-all active:scale-95"
      >
        <Loader2 v-if="isMerging" class="w-4 h-4 animate-spin" />
        <Download v-else class="w-4 h-4" />
        {{ isMerging ? '正在处理...' : '下载合并表' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 10px;
}
</style>
