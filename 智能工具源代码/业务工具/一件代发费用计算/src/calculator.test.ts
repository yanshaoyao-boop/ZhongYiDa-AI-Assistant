import { describe, expect, it } from 'vitest';
import { calculateQuote } from './pricing';
import type { QuoteInput } from './types';

const baseInput: QuoteInput = {
  businessMode: 'dropshipping-only',
  inboundType: 'fcl',
  containerType: '20GP',
  boxCount: 50,
  pieceCount: 100,
  lengthCm: 40,
  widthCm: 30,
  heightCm: 20,
  actualWeightKg: 3,
  hasThirdPartyLabel: false,
  storageType: 'sellable',
  storageDays: 50,
  hasMixedSku: false,
  selectedServices: []
};

describe('calculateQuote', () => {
  it('uses the higher of actual and volumetric weight, then converts to lb', () => {
    const result = calculateQuote(baseInput);

    expect(result.weights.actualWeightKg).toBe(3);
    expect(result.weights.volumetricWeightKg).toBe(4);
    expect(result.weights.chargeableWeightKg).toBe(4);
    expect(result.weights.chargeableWeightLb).toBeCloseTo(8.81849, 5);
    expect(result.weights.matchedBracket).toBe('5-10 LB');
  });

  it('waives unloading for headhaul plus dropshipping', () => {
    const result = calculateQuote({
      ...baseInput,
      businessMode: 'headhaul-plus-dropshipping'
    });

    expect(result.inboundTotal).toBeCloseTo(50, 2);
    expect(result.feeLines.find((line) => line.name === '卸货费')?.amount).toBe(0);
  });

  it('charges over-carton surcharge only on boxes above 800 for lcl', () => {
    const result = calculateQuote({
      ...baseInput,
      inboundType: 'lcl',
      containerType: undefined,
      boxCount: 850
    });

    expect(result.feeLines.find((line) => line.name === '散货卸货费')?.amount).toBe(1700);
    expect(result.feeLines.find((line) => line.name === '超箱附加费')?.amount).toBe(15);
  });

  it('adds sellable storage only after the first 30 days', () => {
    const result = calculateQuote(baseInput);

    expect(result.storageTotal).toBeCloseTo(28.8, 2);
  });

  it('marks manual value-added services and excludes them from automatic totals', () => {
    const result = calculateQuote({
      ...baseInput,
      selectedServices: [
        { serviceCode: 'labeling-sku', quantity: 10 },
        { serviceCode: 'custom-request', quantity: 1 }
      ]
    });

    expect(result.valueAddedTotal).toBe(4);
    expect(result.manualItems).toContain('其他定制需求');
  });

  it('charges continuation pricing above 20 lb for inbound and outbound handling', () => {
    const result = calculateQuote({
      ...baseInput,
      pieceCount: 2,
      lengthCm: 30,
      widthCm: 30,
      heightCm: 30,
      actualWeightKg: 15
    });

    expect(result.weights.chargeableWeightLb).toBeGreaterThan(20);
    expect(result.feeLines.find((line) => line.name === '入库上架费')?.amount).toBeCloseTo(5.2277, 3);
    expect(result.feeLines.find((line) => line.name === '出库操作费')?.amount).toBeCloseTo(5.2277, 3);
  });

  it('charges higher third-party label handling for shipments over 10 lb', () => {
    const result = calculateQuote({
      ...baseInput,
      hasThirdPartyLabel: true
    });

    expect(result.feeLines.find((line) => line.name === '平台面单操作费')?.amount).toBe(0.2);

    const heavyResult = calculateQuote({
      ...baseInput,
      actualWeightKg: 12,
      hasThirdPartyLabel: true
    });

    expect(heavyResult.feeLines.find((line) => line.name === '平台面单操作费')?.amount).toBe(0.3);
  });
});
