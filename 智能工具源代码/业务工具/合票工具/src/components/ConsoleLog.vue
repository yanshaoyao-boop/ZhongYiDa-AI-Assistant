<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import type { ProcessingLog } from '../utils/excel-handler';

const props = defineProps<{
  logs: ProcessingLog[];
}>();

const logContainer = ref<HTMLElement | null>(null);

watch(() => props.logs.length, () => {
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight;
    }
  });
});
</script>

<template>
  <div class="glass-card flex flex-col h-64 overflow-hidden mt-6">
    <div class="px-4 py-2 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
      <h3 class="text-sm font-medium text-slate-600">处理日志</h3>
      <span class="text-[10px] text-slate-400 uppercase tracking-wider font-bold">Console Output</span>
    </div>
    <div 
      ref="logContainer"
      class="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-2 selection:bg-brand-100"
    >
      <div v-for="(log, idx) in logs" :key="idx" class="flex gap-3 group">
        <span class="text-slate-400 shrink-0">[{{ log.time }}]</span>
        <span :class="{
          'text-emerald-600': log.type === 'success',
          'text-rose-600': log.type === 'error',
          'text-amber-600': log.type === 'warn',
          'text-slate-600': log.type === 'info'
        }" class="break-all">{{ log.msg }}</span>
      </div>
      <div v-if="logs.length === 0" class="h-full flex items-center justify-center text-slate-400 italic">
        等待任务开始...
      </div>
    </div>
  </div>
</template>
