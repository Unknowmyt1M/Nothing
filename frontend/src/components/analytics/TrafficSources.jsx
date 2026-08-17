'use client';
import { motion } from 'framer-motion';
import BarChart from './BarChart';
import ChartCard from './ChartCard';

const DEVICE_ICONS = {
  mobile: 'fa-solid fa-mobile-screen',
  desktop: 'fa-solid fa-desktop',
  tablet: 'fa-solid fa-tablet-screen-button',
  tv: 'fa-solid fa-tv',
  game_console: 'fa-solid fa-gamepad',
};

const COUNTRY_FLAGS = {
  US: '\u{1F1FA}\u{1F1F8}', GB: '\u{1F1EC}\u{1F1E7}', IN: '\u{1F1EE}\u{1F1F3}',
  DE: '\u{1F1E9}\u{1F1EA}', FR: '\u{1F1EB}\u{1F1F7}', BR: '\u{1F1E7}\u{1F1F7}',
  JP: '\u{1F1EF}\u{1F1F5}', CA: '\u{1F1E8}\u{1F1E6}', AU: '\u{1F1E6}\u{1F1FA}',
  MX: '\u{1F1F2}\u{1F1FD}', IT: '\u{1F1EE}\u{1F1F9}', ES: '\u{1F1EA}\u{1F1F8}',
  RU: '\u{1F1F7}\u{1F1FA}', KR: '\u{1F1F0}\u{1F1F7}', NL: '\u{1F1F3}\u{1F1F1}',
  SE: '\u{1F1F8}\u{1F1EA}', PL: '\u{1F1F5}\u{1F1F1}', ID: '\u{1F1EE}\u{1F1E9}',
  PH: '\u{1F1F5}\u{1F1ED}', TH: '\u{1F1F9}\u{1F1ED}', TR: '\u{1F1F9}\u{1F1F7}',
  AR: '\u{1F1E6}\u{1F1F7}', CO: '\u{1F1E8}\u{1F1F4}', ZA: '\u{1F1FF}\u{1F1E6}',
  NG: '\u{1F1F3}\u{1F1EC}', EG: '\u{1F1EA}\u{1F1EC}', PK: '\u{1F1F5}\u{1F1F0}',
  BD: '\u{1F1E7}\u{1F1E9}', VN: '\u{1F1FB}\u{1F1F3}', MY: '\u{1F1F2}\u{1F1FE}',
};

function formatNumber(n) {
  if (n == null) return '—';
  return new Intl.NumberFormat('en-US').format(n);
}

export default function TrafficSources({ traffic, audience }) {
  const trafficLoading = traffic?.loading;
  const trafficError = traffic?.error;
  const trafficData = traffic?.data;
  const audienceData = audience?.data;

  const sources = trafficData?.sources || trafficData?.traffic_sources || [];
  const countries = trafficData?.countries || audienceData?.countries || [];
  const devices = trafficData?.devices || audienceData?.devices || [];

  const sourceChartData = sources.map((s) => ({
    label: s.source || s.name || 'Unknown',
    value: s.visits || s.value || s.count || 0,
    color: s.source === 'YouTube search' ? 'var(--color-cyan)' : s.source === 'Suggested videos' ? 'var(--color-pink)' : s.source === 'External' ? 'var(--color-purple)' : undefined,
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Traffic Sources */}
      <ChartCard title="Traffic Sources" subtitle="How viewers find your content">
        {trafficLoading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {[1, 2, 3, 4, 5].map((n) => (
              <div
                key={n}
                style={{
                  height: '22px',
                  borderRadius: '6px',
                  background: 'rgba(255,255,255,0.05)',
                  animation: 'pulse 1.5s infinite',
                }}
              />
            ))}
          </div>
        ) : trafficError ? (
          <p style={{ color: 'var(--color-pink)', fontSize: '14px' }}>
            Unable to load traffic sources
          </p>
        ) : (
          <BarChart data={sourceChartData} maxItems={8} />
        )}
      </ChartCard>

      {/* Top Countries */}
      {countries.length > 0 && (
        <ChartCard title="Top Countries" subtitle="Viewer geographic distribution">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {countries.slice(0, 10).map((c, i) => {
              const code = (c.country_code || c.code || '').toUpperCase();
              const flag = COUNTRY_FLAGS[code] || '';
              const totalViews = countries.reduce(
                (sum, x) => sum + (x.views || x.value || x.count || 0),
                0
              );
              const pct = totalViews > 0
                ? ((c.views || c.value || c.count || 0) / totalViews) * 100
                : 0;

              return (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                  }}
                >
                  <span style={{ fontSize: '18px', lineHeight: 1 }}>{flag}</span>
                  <span
                    style={{
                      flex: 1,
                      fontSize: '14px',
                      color: 'var(--color-text-secondary)',
                    }}
                  >
                    {c.country || c.name || code || 'Unknown'}
                  </span>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '13px',
                      fontWeight: '600',
                      color: 'var(--color-text-primary)',
                    }}
                  >
                    {formatNumber(c.views || c.value || c.count)}
                  </span>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '12px',
                      color: 'var(--color-text-muted)',
                      minWidth: '45px',
                      textAlign: 'right',
                    }}
                  >
                    {pct.toFixed(1)}%
                  </span>
                </div>
              );
            })}
          </div>
        </ChartCard>
      )}

      {/* Device Breakdown */}
      {devices.length > 0 && (
        <ChartCard title="Device Breakdown" subtitle="Viewing device types">
          <div
            style={{
              display: 'flex',
              gap: '16px',
              flexWrap: 'wrap',
            }}
          >
            {devices.map((d, i) => {
              const deviceType = (d.device || d.type || 'unknown').toLowerCase();
              const icon = DEVICE_ICONS[deviceType] || 'fa-solid fa-circle-question';
              const totalViews = devices.reduce(
                (sum, x) => sum + (x.views || x.value || x.count || 0),
                0
              );
              const pct = totalViews > 0
                ? ((d.views || d.value || d.count || 0) / totalViews) * 100
                : 0;

              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.08 }}
                  className="glass-panel"
                  style={{
                    padding: '20px',
                    flex: '1 1 140px',
                    textAlign: 'center',
                  }}
                >
                  <i
                    className={icon}
                    style={{
                      fontSize: '24px',
                      color: 'var(--color-cyan)',
                      marginBottom: '10px',
                      display: 'block',
                    }}
                  />
                  <div
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '20px',
                      fontWeight: '700',
                      color: 'var(--color-text-primary)',
                    }}
                  >
                    {pct.toFixed(1)}%
                  </div>
                  <div
                    style={{
                      fontSize: '12px',
                      color: 'var(--color-text-muted)',
                      textTransform: 'capitalize',
                      marginTop: '4px',
                    }}
                  >
                    {deviceType}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </ChartCard>
      )}
    </div>
  );
}
