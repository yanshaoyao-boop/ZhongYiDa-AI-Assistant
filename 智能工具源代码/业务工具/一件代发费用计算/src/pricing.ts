import {
  FCL_UNLOADING_FEES,
  HANDLING_TIERS,
  LB_PER_KG,
  LCL_BOX_FEE,
  LCL_OVER_CARTON_SURCHARGE,
  LCL_OVER_CARTON_THRESHOLD,
  MIXED_SKU_SURCHARGE,
  NON_SELLABLE_STORAGE_TIERS,
  OUTBOUND_TIERS,
  SELLABLE_STORAGE_TIERS,
  THIRD_PARTY_LABEL_RATES,
  VALUE_ADDED_SERVICES,
  type StorageTier,
  type TierRate
} from './data';
import type { FeeLine, QuoteInput, QuoteResult, WeightResult } from './types';

function roundCurrency(value: number) {
  return Math.round(value * 100) / 100;
}

function calculateVolumeCbm(input: QuoteInput) {
  const rawVolume = (input.lengthCm * input.widthCm * input.heightCm) / 1_000_000;
  return Math.max(rawVolume, 0.001) * input.pieceCount;
}

function getTierLabel(weightLb: number) {
  if (weightLb <= 2) return '0-2 LB';
  if (weightLb <= 5) return '2-5 LB';
  if (weightLb <= 10) return '5-10 LB';
  if (weightLb <= 20) return '10-20 LB';
  return '20+ LB';
}

function computeWeights(input: QuoteInput): WeightResult {
  const volumetricWeightKg = (input.lengthCm * input.widthCm * input.heightCm) / 6000;
  const chargeableWeightKg = Math.max(input.actualWeightKg, volumetricWeightKg);
  const chargeableWeightLb = chargeableWeightKg * LB_PER_KG;

  return {
    actualWeightKg: input.actualWeightKg,
    volumetricWeightKg,
    chargeableWeightKg,
    chargeableWeightLb,
    matchedBracket: getTierLabel(chargeableWeightLb)
  };
}

function resolvePieceHandlingAmount(tiers: TierRate[], chargeableWeightLb: number, pieceCount: number) {
  const fixedTier = tiers.find((tier) => tier.maxLb !== undefined && chargeableWeightLb <= tier.maxLb);
  if (fixedTier?.unitPrice !== undefined) {
    return {
      amount: fixedTier.unitPrice * pieceCount,
      unitPrice: fixedTier.unitPrice,
      formula: `${fixedTier.unitPrice.toFixed(2)} × ${pieceCount}`,
      bracket: fixedTier.label
    };
  }

  const continuationTier = tiers.find((tier) => tier.continuationPrice !== undefined);
  const extraLb = Math.max(chargeableWeightLb - 20, 0);
  const unitPrice = continuationTier?.continuationPrice ?? 0;

  return {
    amount: extraLb * unitPrice * pieceCount,
    unitPrice,
    formula: `(${chargeableWeightLb.toFixed(2)} - 20) × ${unitPrice.toFixed(2)} × ${pieceCount}`,
    bracket: continuationTier?.label ?? '20+ LB'
  };
}

function calculateProgressiveStorage(totalCbm: number, storageDays: number, tiers: StorageTier[]) {
  return tiers.reduce((sum, tier) => {
    if (storageDays < tier.startDay) {
      return sum;
    }

    const effectiveEnd = tier.endDay ?? storageDays;
    const actualEnd = Math.min(storageDays, effectiveEnd);
    const daysInTier = Math.max(actualEnd - tier.startDay + 1, 0);

    return sum + totalCbm * daysInTier * tier.rate;
  }, 0);
}

function createFeeLine(line: FeeLine): FeeLine {
  return line;
}

export function calculateQuote(input: QuoteInput): QuoteResult {
  const weights = computeWeights(input);
  const feeLines: FeeLine[] = [];
  const manualItems: string[] = [];

  const unloadingFee =
    input.businessMode === 'headhaul-plus-dropshipping'
      ? 0
      : input.inboundType === 'fcl'
        ? input.containerType
          ? FCL_UNLOADING_FEES[input.containerType]
          : 0
        : (input.boxCount ?? 0) * LCL_BOX_FEE;

  feeLines.push(
    createFeeLine({
      module: 'inbound',
      name: input.inboundType === 'fcl' ? '卸货费' : '散货卸货费',
      formulaText:
        input.businessMode === 'headhaul-plus-dropshipping'
          ? '头程+一件代发免卸货费'
          : input.inboundType === 'fcl'
            ? `${input.containerType ?? ''} 固定柜型费`
            : `${input.boxCount ?? 0} 箱 × ${LCL_BOX_FEE.toFixed(2)}`,
      unitPrice: input.inboundType === 'fcl' ? unloadingFee : LCL_BOX_FEE,
      quantity: input.inboundType === 'fcl' ? 1 : input.boxCount ?? 0,
      amount: unloadingFee,
      isManual: false
    })
  );

  if (input.inboundType === 'lcl') {
    const extraBoxes = Math.max((input.boxCount ?? 0) - LCL_OVER_CARTON_THRESHOLD, 0);
    const overCartonAmount = extraBoxes * LCL_OVER_CARTON_SURCHARGE;
    feeLines.push(
      createFeeLine({
        module: 'inbound',
        name: '超箱附加费',
        formulaText: `${extraBoxes} 箱 × ${LCL_OVER_CARTON_SURCHARGE.toFixed(2)}`,
        unitPrice: LCL_OVER_CARTON_SURCHARGE,
        quantity: extraBoxes,
        amount: overCartonAmount,
        isManual: false
      })
    );
  }

  const inboundHandling = resolvePieceHandlingAmount(HANDLING_TIERS, weights.chargeableWeightLb, input.pieceCount);
  feeLines.push(
    createFeeLine({
      module: 'inbound',
      name: '入库上架费',
      formulaText: inboundHandling.formula,
      unitPrice: inboundHandling.unitPrice,
      quantity: input.pieceCount,
      amount: inboundHandling.amount,
      isManual: false,
      note: inboundHandling.bracket
    })
  );

  if (input.hasMixedSku) {
    feeLines.push(
      createFeeLine({
        module: 'inbound',
        name: '混 SKU 附加费',
        formulaText: `${input.pieceCount} 件 × ${MIXED_SKU_SURCHARGE.toFixed(2)}`,
        unitPrice: MIXED_SKU_SURCHARGE,
        quantity: input.pieceCount,
        amount: input.pieceCount * MIXED_SKU_SURCHARGE,
        isManual: false
      })
    );
  }

  const outboundHandling = resolvePieceHandlingAmount(OUTBOUND_TIERS, weights.chargeableWeightLb, input.pieceCount);
  feeLines.push(
    createFeeLine({
      module: 'outbound',
      name: '出库操作费',
      formulaText: outboundHandling.formula,
      unitPrice: outboundHandling.unitPrice,
      quantity: input.pieceCount,
      amount: outboundHandling.amount,
      isManual: false,
      note: outboundHandling.bracket
    })
  );

  if (input.hasThirdPartyLabel) {
    const unitPrice =
      weights.chargeableWeightLb <= 10
        ? THIRD_PARTY_LABEL_RATES.underOrEqual10Lb
        : THIRD_PARTY_LABEL_RATES.over10Lb;
    feeLines.push(
      createFeeLine({
        module: 'outbound',
        name: '平台面单操作费',
        formulaText: `${unitPrice.toFixed(2)} × 1 单`,
        unitPrice,
        quantity: 1,
        amount: unitPrice,
        isManual: false
      })
    );
  }

  const totalCbm = calculateVolumeCbm(input);
  if (input.storageType && input.storageDays && input.storageDays > 0) {
    const storageAmount =
      input.storageType === 'sellable'
        ? calculateProgressiveStorage(totalCbm, input.storageDays, SELLABLE_STORAGE_TIERS)
        : calculateProgressiveStorage(totalCbm, input.storageDays, NON_SELLABLE_STORAGE_TIERS);
    feeLines.push(
      createFeeLine({
        module: 'storage',
        name: input.storageType === 'sellable' ? '可售库存仓储费' : '不可售库存仓储费',
        formulaText: `${totalCbm.toFixed(3)} CBM × ${input.storageDays} 天 阶梯计费`,
        unitPrice: null,
        quantity: input.storageDays,
        amount: storageAmount,
        isManual: false
      })
    );
  }

  for (const selectedService of input.selectedServices) {
    const service = VALUE_ADDED_SERVICES.find((item) => item.code === selectedService.serviceCode);
    if (!service) {
      continue;
    }

    if (service.manual || service.price === null) {
      manualItems.push(service.name);
      feeLines.push(
        createFeeLine({
          module: 'valueAdded',
          name: service.name,
          formulaText: '人工确认',
          unitPrice: null,
          quantity: selectedService.quantity,
          amount: 0,
          isManual: true,
          note: service.note
        })
      );
      continue;
    }

    const normalizedQuantity =
      service.code === 'special-labor'
        ? Math.max(selectedService.quantity, 0.5)
        : selectedService.quantity;
    const amountBase = service.price * normalizedQuantity;
    const weightedAmount =
      service.weightContinuationPrice && weights.chargeableWeightLb > 20
        ? amountBase +
          (weights.chargeableWeightLb - 20) *
            service.weightContinuationPrice *
            selectedService.quantity
        : amountBase;
    const amount = service.minimumTotal ? Math.max(weightedAmount, service.minimumTotal) : weightedAmount;

    feeLines.push(
      createFeeLine({
        module: 'valueAdded',
        name: service.name,
        formulaText: `${normalizedQuantity} ${service.unitLabel} × ${service.price.toFixed(2)}`,
        unitPrice: service.price,
        quantity: normalizedQuantity,
        amount,
        isManual: false,
        note: service.note
      })
    );
  }

  const inboundTotal = roundCurrency(
    feeLines.filter((line) => line.module === 'inbound' && !line.isManual).reduce((sum, line) => sum + line.amount, 0)
  );
  const outboundTotal = roundCurrency(
    feeLines.filter((line) => line.module === 'outbound' && !line.isManual).reduce((sum, line) => sum + line.amount, 0)
  );
  const storageTotal = roundCurrency(
    feeLines.filter((line) => line.module === 'storage' && !line.isManual).reduce((sum, line) => sum + line.amount, 0)
  );
  const valueAddedTotal = roundCurrency(
    feeLines.filter((line) => line.module === 'valueAdded' && !line.isManual).reduce((sum, line) => sum + line.amount, 0)
  );
  const grandTotal = roundCurrency(inboundTotal + outboundTotal + storageTotal + valueAddedTotal);

  return {
    weights,
    inboundTotal,
    outboundTotal,
    storageTotal,
    valueAddedTotal,
    grandTotal,
    unitCost: input.pieceCount > 0 ? roundCurrency(grandTotal / input.pieceCount) : 0,
    feeLines,
    manualItems
  };
}
