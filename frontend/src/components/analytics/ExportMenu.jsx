'use client';
import { useState, useRef, useEffect } from 'react';

export default function ExportMenu({ channelId, startDate, endDate }) {
  const [open, setOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleExport = async (format) => {
    if (!channelId) return;
    setExporting(true);
    try {
      const url = `/api/analytics/export?channel_id=${channelId}&start_date=${startDate}&end_date=${endDate}&format=${format}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Export failed');

      const blob = await res.blob();
      const downloadUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `analytics-${channelId}-${startDate}-to-${endDate}.${format === 'json' ? 'json' : 'csv'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error('Export error:', err);
    } finally {
      setExporting(false);
      setOpen(false);
    }
  };

  return (
    <div ref={menuRef} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          padding: '8px 16px',
          borderRadius: '8px',
          border: '1px solid var(--color-border)',
          background: 'var(--bg-card)',
          color: 'var(--color-text-secondary)',
          fontSize: '13px',
          fontWeight: '600',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          backdropFilter: 'var(--glass-blur)',
          WebkitBackdropFilter: 'var(--glass-blur)',
          transition: 'all 0.2s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = 'rgba(0, 242, 254, 0.3)';
          e.currentTarget.style.color = 'var(--color-cyan)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = 'var(--color-border)';
          e.currentTarget.style.color = 'var(--color-text-secondary)';
        }}
      >
        <i className="fa-solid fa-download" style={{ fontSize: '12px' }} />
        {exporting ? 'Exporting...' : 'Export'}
      </button>

      {open && (
        <div
          className="glass-panel"
          style={{
            position: 'absolute',
            top: '100%',
            right: 0,
            marginTop: '6px',
            minWidth: '140px',
            zIndex: 50,
            padding: '6px',
          }}
        >
          {['csv', 'json'].map((fmt) => (
            <button
              key={fmt}
              onClick={() => handleExport(fmt)}
              style={{
                width: '100%',
                padding: '10px 16px',
                border: 'none',
                background: 'transparent',
                color: 'var(--color-text-secondary)',
                fontSize: '13px',
                fontWeight: '500',
                cursor: 'pointer',
                textAlign: 'left',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(0, 242, 254, 0.08)';
                e.currentTarget.style.color = 'var(--color-cyan)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'transparent';
                e.currentTarget.style.color = 'var(--color-text-secondary)';
              }}
            >
              <i
                className={
                  fmt === 'csv'
                    ? 'fa-solid fa-file-csv'
                    : 'fa-solid fa-file-code'
                }
                style={{ fontSize: '13px', width: '18px', textAlign: 'center' }}
              />
              {fmt.toUpperCase()}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
