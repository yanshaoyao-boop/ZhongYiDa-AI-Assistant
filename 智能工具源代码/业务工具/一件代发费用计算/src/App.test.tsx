import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import App from './App';

describe('App', () => {
  it('renders localized module labels instead of internal enum values', () => {
    const markup = renderToStaticMarkup(<App />);

    expect(markup).toContain('>入库<');
    expect(markup).toContain('>出库<');
    expect(markup).toContain('>仓储<');
    expect(markup).toContain('>增值服务<');
    expect(markup).not.toContain('>inbound<');
    expect(markup).not.toContain('>outbound<');
    expect(markup).not.toContain('>storage<');
    expect(markup).not.toContain('>valueAdded<');
  });
});
