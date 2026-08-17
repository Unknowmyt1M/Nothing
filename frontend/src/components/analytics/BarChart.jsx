'use client';
import { motion } from 'framer-motion';

export default function BarChart({ data = [], maxItems = 10 }) {
  const sliced = data.slice(0, maxItems);
  const maxValue = Math.max(...sliced.map((d) => d.value), 1);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {sliced.map((item, i) => {
        const pct = (item.value / maxValue) * 100;
        const barColor = item.color || 'var(--color-cyan)';

        return (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <span
              style={{
                fontSize: '13px',
                color: 'var(--color-text-secondary)',
                minWidth: '120px',
                maxWidth: '120px',
                textAlign: 'right',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {item.label}
            </span>
            <div
              style={{
                flex: 1,
                height: '22px',
                background: 'rgba(255,255,255,0.04)',
                borderRadius: '6px',
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.6, ease: 'easeOut', delay: i * 0.05 }}
                style={{
                  height: '100%',
                  background: barColor,
                  borderRadius: '6px',
                  opacity: 0.8,
                }}
              />
            </div>
            <span
              style={{
                fontSize: '13px',
                fontFamily: 'var(--font-mono)',
                fontWeight: '600',
                color: 'var(--color-text-primary)',
                minWidth: '60px',
                textAlign: 'right',
              }}
            >
              {new Intl.NumberFormat('en-US').format(item.value)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
