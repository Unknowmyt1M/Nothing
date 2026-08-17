'use client';
import { useState } from 'react';

function getDateRange(preset) {
  const now = new Date();
  const start = new Date();
  const end = new Date(now);

  switch (preset) {
    case '7D':
      start.setDate(now.getDate() - 7);
      return { start: start.toISOString().split('T')[0], end: end.toISOString().split('T')[0], label: 'Last 7 Days' };
    case '28D':
      start.setDate(now.getDate() - 28);
      return { start: start.toISOString().split('T')[0], end: end.toISOString().split('T')[0], label: 'Last 28 Days' };
    case '30D':
      start.setDate(now.getDate() - 30);
      return { start: start.toISOString().split('T')[0], end: end.toISOString().split('T')[0], label: 'Last 30 Days' };
    case '90D':
      start.setDate(now.getDate() - 90);
      return { start: start.toISOString().split('T')[0], end: end.toISOString().split('T')[0], label: 'Last 90 Days' };
    case '1Y':
      start.setFullYear(now.getFullYear() - 1);
      return { start: start.toISOString().split('T')[0], end: end.toISOString().split('T')[0], label: 'Last 12 Months' };
    case 'TY':
      start.setMonth(0, 1);
      return { start: start.toISOString().split('T')[0], end: end.toISOString().split('T')[0], label: 'This Year' };
    case 'LY':
      start.setFullYear(now.getFullYear() - 1, 0, 1);
      end.setFullYear(now.getFullYear() - 1, 11, 31);
      return { start: start.toISOString().split('T')[0], end: end.toISOString().split('T')[0], label: 'Last Year' };
    default:
      start.setDate(now.getDate() - 28);
      return { start: start.toISOString().split('T')[0], end: end.toISOString().split('T')[0], label: 'Last 28 Days' };
  }
}

const PRESETS = ['7D', '28D', '30D', '90D', '1Y', 'TY', 'LY'];

const PRESET_LABELS = {
  '7D': '7D',
  '28D': '28D',
  '30D': '30D',
  '90D': '90D',
  '1Y': '1Y',
  'TY': 'This Year',
  'LY': 'Last Year',
};

export default function DateRangeSelector({ onChange, activePreset = '28D' }) {
  const [active, setActive] = useState(activePreset);

  const handleSelect = (preset) => {
    setActive(preset);
    const range = getDateRange(preset);
    onChange(range.start, range.end, range.label);
  };

  return (
    <div
      style={{
        display: 'flex',
        gap: '8px',
        overflowX: 'auto',
        paddingBottom: '4px',
        scrollbarWidth: 'none',
      }}
    >
      {PRESETS.map((preset) => (
        <button
          key={preset}
          onClick={() => handleSelect(preset)}
          style={{
            padding: '8px 18px',
            borderRadius: '8px',
            border: active === preset ? '1px solid var(--color-cyan)' : '1px solid var(--color-border)',
            background: active === preset
              ? 'rgba(0, 242, 254, 0.15)'
              : 'var(--bg-card)',
            color: active === preset ? 'var(--color-cyan)' : 'var(--color-text-secondary)',
            fontFamily: 'var(--font-mono)',
            fontSize: '13px',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            whiteSpace: 'nowrap',
            backdropFilter: 'var(--glass-blur)',
            WebkitBackdropFilter: 'var(--glass-blur)',
            boxShadow: active === preset ? 'var(--neon-shadow-cyan)' : 'none',
          }}
        >
          {PRESET_LABELS[preset]}
        </button>
      ))}
    </div>
  );
}
