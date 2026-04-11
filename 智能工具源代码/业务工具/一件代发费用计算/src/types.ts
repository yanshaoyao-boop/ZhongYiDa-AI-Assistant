export type BusinessMode = 'headhaul-plus-dropshipping' | 'dropshipping-only';
export type InboundType = 'fcl' | 'lcl';
export type ContainerType = '20GP' | '40HQ' | '45HQ';
export type StorageType = 'sellable' | 'non-sellable';

export interface SelectedServiceInput {
  serviceCode: string;
  quantity: number;
}

export interface SelectedServiceResult extends SelectedServiceInput {
  serviceName: string;
  unitLabel: string;
}

export interface QuoteInput {
  businessMode: BusinessMode;
  inboundType: InboundType;
  containerType?: ContainerType;
  boxCount?: number;
  pieceCount: number;
  lengthCm: number;
  widthCm: number;
  heightCm: number;
  actualWeightKg: number;
  hasThirdPartyLabel: boolean;
  storageType?: StorageType;
  storageDays?: number;
  hasMixedSku?: boolean;
  selectedServices: SelectedServiceInput[];
}

export interface WeightResult {
  actualWeightKg: number;
  volumetricWeightKg: number;
  chargeableWeightKg: number;
  chargeableWeightLb: number;
  matchedBracket: string;
}

export interface FeeLine {
  module: 'inbound' | 'outbound' | 'storage' | 'valueAdded';
  name: string;
  formulaText: string;
  unitPrice: number | null;
  quantity: number;
  amount: number;
  isManual: boolean;
  note?: string;
}

export interface QuoteResult {
  weights: WeightResult;
  inboundTotal: number;
  outboundTotal: number;
  storageTotal: number;
  valueAddedTotal: number;
  grandTotal: number;
  unitCost: number;
  feeLines: FeeLine[];
  manualItems: string[];
}
