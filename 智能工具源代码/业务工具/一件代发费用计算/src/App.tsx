import { startTransition, useState } from 'react';
import { VALUE_ADDED_SERVICES } from './data';
import { calculateQuote } from './pricing';
import type {
  BusinessMode,
  ContainerType,
  FeeLine,
  InboundType,
  QuoteInput,
  SelectedServiceInput,
  StorageType
} from './types';

const groupedServices = VALUE_ADDED_SERVICES.reduce<Record<string, typeof VALUE_ADDED_SERVICES>>((acc, service) => {
  acc[service.group] = acc[service.group] ? [...acc[service.group], service] : [service];
  return acc;
}, {});

const moduleLabels: Record<FeeLine['module'], string> = {
  inbound: '入库',
  outbound: '出库',
  storage: '仓储',
  valueAdded: '增值服务'
};

const defaultInput: QuoteInput = {
  businessMode: 'dropshipping-only',
  inboundType: 'fcl',
  containerType: '20GP',
  boxCount: 100,
  pieceCount: 120,
  lengthCm: 40,
  widthCm: 30,
  heightCm: 20,
  actualWeightKg: 3,
  hasThirdPartyLabel: false,
  storageType: 'sellable',
  storageDays: 45,
  hasMixedSku: false,
  selectedServices: [
    {
      serviceCode: 'labeling-sku',
      quantity: 120
    }
  ]
};

function updateNumber(value: string, fallback = 0) {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

function formatNumber(value: number) {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

function App() {
  const [form, setForm] = useState<QuoteInput>(defaultInput);
  const quote = calculateQuote(form);

  const setField = <K extends keyof QuoteInput>(field: K, value: QuoteInput[K]) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleInboundType = (value: InboundType) => {
    setForm((current) => ({
      ...current,
      inboundType: value,
      containerType: value === 'fcl' ? current.containerType ?? '20GP' : undefined,
      boxCount: value === 'lcl' ? current.boxCount ?? 0 : current.boxCount
    }));
  };

  const handleStorageToggle = (enabled: boolean) => {
    setForm((current) => ({
      ...current,
      storageType: enabled ? current.storageType ?? 'sellable' : undefined,
      storageDays: enabled ? current.storageDays ?? 45 : undefined
    }));
  };

  const updateService = (index: number, patch: Partial<SelectedServiceInput>) => {
    startTransition(() => {
      setForm((current) => ({
        ...current,
        selectedServices: current.selectedServices.map((service, serviceIndex) =>
          serviceIndex === index ? { ...service, ...patch } : service
        )
      }));
    });
  };

  const addService = () => {
    startTransition(() => {
      setForm((current) => ({
        ...current,
        selectedServices: [
          ...current.selectedServices,
          {
            serviceCode: VALUE_ADDED_SERVICES[0].code,
            quantity: 1
          }
        ]
      }));
    });
  };

  const removeService = (index: number) => {
    startTransition(() => {
      setForm((current) => ({
        ...current,
        selectedServices: current.selectedServices.filter((_, serviceIndex) => serviceIndex !== index)
      }));
    });
  };

  return (
    <div className="app-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />
      <header className="hero">
        <div>
          <p className="eyebrow">ZYD USA WAREHOUSE</p>
          <h1>美国一件代发报价计算器</h1>
          <p className="hero-copy">
            内部销售工作台。统一按 cm / kg 录入，自动换算 lb 命中价格档位，并输出入库、出库、仓储和增值服务的拆项报价。
          </p>
        </div>
        <div className="hero-strip">
          <div>
            <span>计费重</span>
            <strong>{formatNumber(quote.weights.chargeableWeightLb)} LB</strong>
          </div>
          <div>
            <span>命中档位</span>
            <strong>{quote.weights.matchedBracket}</strong>
          </div>
          <div>
            <span>总报价</span>
            <strong>{formatCurrency(quote.grandTotal)}</strong>
          </div>
        </div>
      </header>

      <main className="workspace">
        <section className="panel panel-form">
          <div className="section-heading">
            <span>报价输入</span>
            <p>按单个 SKU / 批次录入，右侧会实时给出拆项报价。</p>
          </div>

          <div className="form-grid">
            <label className="field">
              <span>业务模式</span>
              <select
                value={form.businessMode}
                onChange={(event) => setField('businessMode', event.target.value as BusinessMode)}
              >
                <option value="dropshipping-only">单纯一件代发</option>
                <option value="headhaul-plus-dropshipping">头程 + 一件代发</option>
              </select>
            </label>

            <label className="field">
              <span>入库类型</span>
              <select
                value={form.inboundType}
                onChange={(event) => handleInboundType(event.target.value as InboundType)}
              >
                <option value="fcl">整柜</option>
                <option value="lcl">散货</option>
              </select>
            </label>

            {form.inboundType === 'fcl' ? (
              <label className="field">
                <span>柜型</span>
                <select
                  value={form.containerType}
                  onChange={(event) => setField('containerType', event.target.value as ContainerType)}
                >
                  <option value="20GP">20GP</option>
                  <option value="40HQ">40HQ</option>
                  <option value="45HQ">45HQ</option>
                </select>
              </label>
            ) : (
              <label className="field">
                <span>箱数</span>
                <input
                  type="number"
                  min="0"
                  value={form.boxCount ?? 0}
                  onChange={(event) => setField('boxCount', updateNumber(event.target.value))}
                />
              </label>
            )}

            <label className="field">
              <span>总件数</span>
              <input
                type="number"
                min="1"
                value={form.pieceCount}
                onChange={(event) => setField('pieceCount', updateNumber(event.target.value, 1))}
              />
            </label>

            <label className="field">
              <span>单件重量 (kg)</span>
              <input
                type="number"
                min="0"
                step="0.01"
                value={form.actualWeightKg}
                onChange={(event) => setField('actualWeightKg', updateNumber(event.target.value))}
              />
            </label>

            <label className="field">
              <span>长 (cm)</span>
              <input
                type="number"
                min="0"
                step="0.1"
                value={form.lengthCm}
                onChange={(event) => setField('lengthCm', updateNumber(event.target.value))}
              />
            </label>

            <label className="field">
              <span>宽 (cm)</span>
              <input
                type="number"
                min="0"
                step="0.1"
                value={form.widthCm}
                onChange={(event) => setField('widthCm', updateNumber(event.target.value))}
              />
            </label>

            <label className="field">
              <span>高 (cm)</span>
              <input
                type="number"
                min="0"
                step="0.1"
                value={form.heightCm}
                onChange={(event) => setField('heightCm', updateNumber(event.target.value))}
              />
            </label>
          </div>

          <div className="toggle-row">
            <label className="checkbox">
              <input
                type="checkbox"
                checked={form.hasMixedSku ?? false}
                onChange={(event) => setField('hasMixedSku', event.target.checked)}
              />
              <span>混 SKU 入库</span>
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={form.hasThirdPartyLabel}
                onChange={(event) => setField('hasThirdPartyLabel', event.target.checked)}
              />
              <span>客户自带平台面单</span>
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={Boolean(form.storageType)}
                onChange={(event) => handleStorageToggle(event.target.checked)}
              />
              <span>计入仓储费</span>
            </label>
          </div>

          {form.storageType ? (
            <div className="form-grid compact-grid">
              <label className="field">
                <span>库存类型</span>
                <select
                  value={form.storageType}
                  onChange={(event) => setField('storageType', event.target.value as StorageType)}
                >
                  <option value="sellable">可售库存</option>
                  <option value="non-sellable">不可售库存</option>
                </select>
              </label>
              <label className="field">
                <span>在库天数</span>
                <input
                  type="number"
                  min="1"
                  value={form.storageDays ?? 45}
                  onChange={(event) => setField('storageDays', updateNumber(event.target.value, 1))}
                />
              </label>
            </div>
          ) : null}

          <div className="section-heading service-heading">
            <span>增值服务</span>
            <p>下拉选择服务项并录入数量。带人工确认标记的项目不会自动计入总价。</p>
          </div>

          <div className="service-list">
            {form.selectedServices.map((selectedService, index) => {
              const current = VALUE_ADDED_SERVICES.find((service) => service.code === selectedService.serviceCode);
              return (
                <div className="service-row" key={`${selectedService.serviceCode}-${index}`}>
                  <label className="field service-select">
                    <span>服务项</span>
                    <select
                      value={selectedService.serviceCode}
                      onChange={(event) => updateService(index, { serviceCode: event.target.value })}
                    >
                      {Object.entries(groupedServices).map(([group, services]) => (
                        <optgroup key={group} label={group}>
                          {services.map((service) => (
                            <option key={service.code} value={service.code}>
                              {service.name}
                            </option>
                          ))}
                        </optgroup>
                      ))}
                    </select>
                  </label>
                  <label className="field service-qty">
                    <span>数量</span>
                    <input
                      type="number"
                      min="0"
                      step={selectedService.serviceCode === 'special-labor' ? '0.5' : '1'}
                      value={selectedService.quantity}
                      onChange={(event) => updateService(index, { quantity: updateNumber(event.target.value) })}
                    />
                  </label>
                  <button className="ghost-button" type="button" onClick={() => removeService(index)}>
                    删除
                  </button>
                  {current?.manual ? <span className="manual-badge">人工确认</span> : null}
                </div>
              );
            })}
            <button className="add-button" type="button" onClick={addService}>
              添加增值服务
            </button>
          </div>
        </section>

        <section className="panel panel-output">
          <div className="section-heading">
            <span>计算过程</span>
            <p>输入使用 kg / cm，价格判断统一落到 lb 档位。</p>
          </div>

          <div className="weight-ribbon">
            <div>
              <label>实重</label>
              <strong>{formatNumber(quote.weights.actualWeightKg)} kg</strong>
            </div>
            <div>
              <label>材积重</label>
              <strong>{formatNumber(quote.weights.volumetricWeightKg)} kg</strong>
            </div>
            <div>
              <label>计费重</label>
              <strong>{formatNumber(quote.weights.chargeableWeightKg)} kg</strong>
            </div>
            <div>
              <label>计费重</label>
              <strong>{formatNumber(quote.weights.chargeableWeightLb)} LB</strong>
            </div>
          </div>

          <div className="summary-grid">
            <article>
              <span>入库费</span>
              <strong>{formatCurrency(quote.inboundTotal)}</strong>
            </article>
            <article>
              <span>出库费</span>
              <strong>{formatCurrency(quote.outboundTotal)}</strong>
            </article>
            <article>
              <span>仓储费</span>
              <strong>{formatCurrency(quote.storageTotal)}</strong>
            </article>
            <article>
              <span>增值服务</span>
              <strong>{formatCurrency(quote.valueAddedTotal)}</strong>
            </article>
          </div>

          <div className="totals-bar">
            <div>
              <span>总报价</span>
              <strong>{formatCurrency(quote.grandTotal)}</strong>
            </div>
            <div>
              <span>单件均摊</span>
              <strong>{formatCurrency(quote.unitCost)}</strong>
            </div>
            <div>
              <span>重量档位</span>
              <strong>{quote.weights.matchedBracket}</strong>
            </div>
          </div>

          <div className="table-shell">
            <table>
              <thead>
                <tr>
                  <th>模块</th>
                  <th>项目</th>
                  <th>计算公式</th>
                  <th>备注</th>
                  <th>金额</th>
                </tr>
              </thead>
              <tbody>
                {quote.feeLines.map((line) => (
                  <tr key={`${line.module}-${line.name}`}>
                    <td>{moduleLabels[line.module]}</td>
                    <td>
                      {line.name}
                      {line.isManual ? <span className="table-manual">人工确认</span> : null}
                    </td>
                    <td>{line.formulaText}</td>
                    <td>{line.note ?? '—'}</td>
                    <td>{line.isManual ? '待确认' : formatCurrency(line.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="manual-box">
            <span>人工确认项</span>
            {quote.manualItems.length > 0 ? (
              <ul>
                {quote.manualItems.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : (
              <p>当前报价全部可自动计算。</p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
