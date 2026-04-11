import type { ContainerType } from './types';

export const LB_PER_KG = 2.20462262;

export interface TierRate {
  label: string;
  maxLb?: number;
  unitPrice?: number;
  continuationPrice?: number;
}

export interface StorageTier {
  startDay: number;
  endDay?: number;
  rate: number;
  label: string;
}

export interface ValueAddedServiceDefinition {
  code: string;
  group: string;
  name: string;
  unitLabel: string;
  price: number | null;
  note?: string;
  minimumTotal?: number;
  manual?: boolean;
  startsAt?: boolean;
  weightContinuationPrice?: number;
}

export const FCL_UNLOADING_FEES: Record<ContainerType, number> = {
  '20GP': 300,
  '40HQ': 380,
  '45HQ': 420
};

export const LCL_BOX_FEE = 2;
export const LCL_OVER_CARTON_THRESHOLD = 800;
export const LCL_OVER_CARTON_SURCHARGE = 0.3;
export const MIXED_SKU_SURCHARGE = 0.3;

export const HANDLING_TIERS: TierRate[] = [
  { label: '0-2 LB', maxLb: 2, unitPrice: 0.3 },
  { label: '2-5 LB', maxLb: 5, unitPrice: 0.4 },
  { label: '5-10 LB', maxLb: 10, unitPrice: 0.5 },
  { label: '10-20 LB', maxLb: 20, unitPrice: 0.6 },
  { label: '20+ LB', continuationPrice: 0.2 }
];

export const OUTBOUND_TIERS: TierRate[] = [
  { label: '0-2 LB', maxLb: 2, unitPrice: 0.5 },
  { label: '2-5 LB', maxLb: 5, unitPrice: 0.6 },
  { label: '5-10 LB', maxLb: 10, unitPrice: 0.7 },
  { label: '10-20 LB', maxLb: 20, unitPrice: 0.8 },
  { label: '20+ LB', continuationPrice: 0.2 }
];

export const THIRD_PARTY_LABEL_RATES = {
  underOrEqual10Lb: 0.2,
  over10Lb: 0.3
};

export const SELLABLE_STORAGE_TIERS: StorageTier[] = [
  { startDay: 1, endDay: 30, rate: 0, label: '1-30 天' },
  { startDay: 31, endDay: 90, rate: 0.6, label: '31-90 天' },
  { startDay: 91, endDay: 120, rate: 1.05, label: '91-120 天' },
  { startDay: 121, endDay: 180, rate: 1.5, label: '121-180 天' },
  { startDay: 181, endDay: 360, rate: 2.35, label: '181-360 天' },
  { startDay: 361, rate: 3.25, label: '361+ 天' }
];

export const NON_SELLABLE_STORAGE_TIERS: StorageTier[] = [
  { startDay: 1, endDay: 15, rate: 0.8, label: '1-15 天' },
  { startDay: 16, endDay: 30, rate: 1.6, label: '16-30 天' },
  { startDay: 31, endDay: 60, rate: 3.2, label: '31-60 天' },
  { startDay: 61, rate: 4.8, label: '61+ 天' }
];

export const VALUE_ADDED_SERVICES: ValueAddedServiceDefinition[] = [
  { code: 'labeling-sku', group: '标签服务', name: '贴标签', unitLabel: '张', price: 0.4, note: '默认覆盖原标' },
  { code: 'relabel', group: '标签服务', name: '换标 / 覆盖原标', unitLabel: '张', price: 0.6 },
  { code: 'outer-box-photo', group: '拍照 / 拍视频', name: '外箱拍照（不开箱）', unitLabel: '张', price: 1, minimumTotal: 3, note: '最低收费 $3 / 次' },
  { code: 'unbox-photo', group: '拍照 / 拍视频', name: '开箱拍照', unitLabel: '张', price: 3, manual: true, note: '超 3 张后按 $1 / 张加收' },
  { code: 'video-shoot', group: '拍照 / 拍视频', name: '拍摄视频', unitLabel: '分钟', price: 5 },
  { code: 'open-box-inspection', group: '仓内操作', name: '开箱检查', unitLabel: '箱', price: 2 },
  { code: 'counting', group: '仓内操作', name: '清点费', unitLabel: '件', price: 0.3 },
  { code: 'reseal-box', group: '仓内操作', name: '封箱费', unitLabel: '箱', price: 0.5 },
  { code: 'palletizing', group: '仓内操作', name: '打托费', unitLabel: '托', price: 18 },
  { code: 'repackaging', group: '仓内操作', name: '重新包装', unitLabel: '件', price: 1, startsAt: true, manual: true, note: '$1 起，按复杂度定价' },
  { code: 'mailer-small', group: '包装材料', name: '快递袋（小）', unitLabel: '个', price: 0.2 },
  { code: 'mailer-medium', group: '包装材料', name: '快递袋（中）', unitLabel: '个', price: 0.25 },
  { code: 'mailer-large', group: '包装材料', name: '快递袋（大）', unitLabel: '个', price: 0.35 },
  { code: 'bubble-small', group: '包装材料', name: '气泡袋（小）', unitLabel: '个', price: 0.6 },
  { code: 'bubble-large', group: '包装材料', name: '气泡袋（大）', unitLabel: '个', price: 1 },
  { code: 'carton-small', group: '包装材料', name: '纸箱（小）', unitLabel: '个', price: 1.5 },
  { code: 'carton-medium', group: '包装材料', name: '纸箱（中）', unitLabel: '个', price: 2.5 },
  { code: 'carton-large', group: '包装材料', name: '纸箱（大）', unitLabel: '个', price: 4 },
  { code: 'returns-reported', group: '退货处理', name: '退货接收（有预报）', unitLabel: '件', price: 2.5 },
  { code: 'returns-unreported', group: '退货处理', name: '退货接收（无预报）', unitLabel: '件', price: 5 },
  { code: 'returns-restock', group: '退货处理', name: '退货重新上架', unitLabel: '件', price: 2 },
  { code: 'returns-disposal', group: '退货处理', name: '退货销毁', unitLabel: '件', price: 1.5, note: '特殊品类另议' },
  { code: 'disposal-general', group: '销毁 / 弃货', name: '普货销毁', unitLabel: '件', price: 1, weightContinuationPrice: 0.15, note: '超 20 LB 按续重' },
  { code: 'disposal-special', group: '销毁 / 弃货', name: '特殊品类销毁', unitLabel: '件', price: null, manual: true, note: '单独询价' },
  { code: 'special-labor', group: '其他特殊服务', name: '人工特殊作业', unitLabel: '人 × 小时', price: 35, note: '最少计费 0.5 小时' },
  { code: 'system-integration', group: '其他特殊服务', name: '系统对接', unitLabel: '单人 / 天', price: 300 },
  { code: 'custom-request', group: '其他特殊服务', name: '其他定制需求', unitLabel: '—', price: null, manual: true, note: '单独询价' }
];
