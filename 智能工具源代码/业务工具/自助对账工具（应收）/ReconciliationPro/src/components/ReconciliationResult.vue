<script setup lang="ts">
import { Download, CheckCircle, AlertTriangle, FileSpreadsheet } from 'lucide-vue-next';
import type { ReconciliationResult } from '../logic/excelProcessor';

interface Props {
  result: ReconciliationResult;
}

defineProps<Props>();
defineEmits(['export-diff', 'export-annotated']);

const formatCurrency = (val: number) => {
  return new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(val);
};
</script>

<template>
  <div class="mt-12 animate-in fade-in slide-in-from-bottom-5 duration-700">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <div class="flex items-center gap-2">
          <component 
            :is="result.isMatch ? CheckCircle : AlertTriangle" 
            :class="result.isMatch ? 'text-emerald-500' : 'text-amber-500'"
            :size="28"
          />
          <h2 class="text-2xl font-bold text-slate-900">
            {{ result.isMatch ? '核对完全一致' : '发现数据差异' }}
          </h2>
        </div>
        <p class="mt-1 text-slate-500">
          共核对 {{ result.totalChecked }} 条数据，其中 {{ result.matchCount }} 条完美匹配
        </p>
      </div>
      
      <div class="flex gap-3">
        <button 
          @click="$emit('export-diff')"
          class="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition-all hover:bg-slate-50 active:scale-95"
        >
          <Download :size="18" />
          导出差异报告
        </button>
        <button 
          @click="$emit('export-annotated')"
          class="flex items-center gap-2 rounded-xl bg-primary-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-primary-200 transition-all hover:bg-primary-700 active:scale-95"
        >
          <FileSpreadsheet :size="18" />
          生成标记原表
        </button>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="mb-8 grid grid-cols-1 gap-6 sm:grid-cols-3">
      <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <p class="text-[11px] font-bold uppercase tracking-widest text-slate-400">业务员总金额</p>
        <p class="mt-2 text-2xl font-bold text-primary-600">{{ formatCurrency(result.totalSalesAmt) }}</p>
      </div>
      <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <p class="text-[11px] font-bold uppercase tracking-widest text-slate-400">代理结算总额</p>
        <p class="mt-2 text-2xl font-bold text-emerald-600">{{ formatCurrency(result.totalAgentAmt) }}</p>
      </div>
      <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <p class="text-[11px] font-bold uppercase tracking-widest text-slate-400">差异总计</p>
        <p 
          class="mt-2 text-2xl font-bold"
          :class="Math.abs(result.totalDiff) < 0.1 ? 'text-slate-900' : 'text-rose-600'"
        >
          {{ formatCurrency(result.totalDiff) }}
        </p>
      </div>
    </div>

    <!-- Discrepancy Table -->
    <div v-if="!result.isMatch" class="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
      <el-table :data="result.discrepancies" style="width: 100%" stripe>
        <el-table-column prop="id" label="单号/编号" min-width="150">
          <template #default="{ row }">
            <span class="font-mono font-medium text-slate-900">{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="client" label="客户" min-width="120">
          <template #default="{ row }">
            <span class="inline-flex rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
              {{ row.client || '未知' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="业务员数据" align="right">
          <template #default="{ row }">
            <div class="font-semibold text-slate-900">{{ formatCurrency(row.sumSales) }}</div>
            <div class="text-[10px] text-slate-400">{{ row.countSales }} 笔汇总</div>
          </template>
        </el-table-column>
        <el-table-column label="代理数据" align="right">
          <template #default="{ row }">
            <div class="font-semibold text-slate-900">{{ formatCurrency(row.sumAgent) }}</div>
            <div class="text-[10px] text-slate-400">来自文件 #{{ row.files.join(', ') }}</div>
          </template>
        </el-table-column>
        <el-table-column label="差额" align="right">
          <template #default="{ row }">
            <span class="font-bold text-rose-600">
              {{ row.diff > 0 ? '+' : '' }}{{ formatCurrency(row.diff) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
:deep(.el-table) {
  --el-table-header-bg-color: #f8fafc;
  --el-table-header-text-color: #64748b;
  font-size: 13px;
}
</style>
