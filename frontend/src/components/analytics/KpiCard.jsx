'use client';
import { motion } from 'framer-motion';

function formatValue(value, label) {
  if (value == null) return '—';
  const num = Number(value);
  if (isNaN(num)) return value;

  if (label && label.toLowerCase().includes('watch time')) {
    const hours = Math.floor(num / 60);
    const mins = num % 60;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
  }

  return new Intl.NumberFormat('en-US').format(num);
}

export default function KpiCard({ icon, value, label, trend, accentColor = 'var(--color-cyan)' }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel"
      style={{
        padding: '24px',
        borderLeft: `4px solid ${accentColor}`,
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: `${accentColor}15`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <i className={icon} style={{ color: accentColor, fontSize: '16px' }} />
        </div>
        <span
          style={{
            fontSize: '13px',
            color: 'var(--color-text-muted)',
            fontWeight: '500',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}
        >
          {label}
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
        <span
          style={{
            fontSize: '28px',
            fontFamily: 'var(--font-mono)',
            fontWeight: '700',
            color: 'var(--color-text-primary)',
          }}
        >
          {formatValue(value, label)}
        </span>
        {trend != null && (
          <span
            style={{
              fontSize: '13px',
              fontFamily: 'var(--font-mono)',
              fontWeight: '600',
              color: trend >= 0 ? '#2ecc71' : 'var(--color-pink)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <i
              className={trend >= 0 ? 'fa-solid fa-arrow-trend-up' : 'fa-solid fa-arrow-trend-down'}
              style={{ fontSize: '11px' }}
            />
            {trend >= 0 ? '+' : ''}{Number(trend).toFixed(1)}%
          </span>
        )}
      </div>
    </motion.div>
  );
}
