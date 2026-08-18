'use client';

export default function Toast({ message, type, onClose }) {
  if (!message) return null;
  
  const icon = type === 'success' ? 'fa-circle-check' : type === 'error' ? 'fa-triangle-exclamation' : 'fa-circle-info';
  const borderCol = type === 'success' ? '#2ecc71' : type === 'error' ? 'var(--color-pink)' : 'var(--color-cyan)';
  const shadowGlow = type === 'success' 
    ? '0 0 15px rgba(46, 204, 113, 0.3)' 
    : type === 'error' 
      ? '0 0 15px rgba(255, 0, 127, 0.3)' 
      : '0 0 15px rgba(0, 242, 254, 0.3)';

  return (
    <div 
      className="cyber-toast" 
      style={{
        borderLeftColor: borderCol,
        boxShadow: `0 4px 20px rgba(0, 0, 0, 0.5), ${shadowGlow}`,
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      }}
    >
      <i className={`fa-solid ${icon}`} style={{ color: borderCol, fontSize: '18px' }}></i>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {type || 'INFO'}
        </span>
        <span style={{ fontSize: '13px', fontWeight: '500', color: '#ffffff' }}>{message}</span>
      </div>
      <button 
        onClick={onClose} 
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--color-text-muted)',
          cursor: 'pointer',
          marginLeft: '15px',
          fontSize: '14px',
        }}
      >
        <i className="fa-solid fa-xmark"></i>
      </button>
    </div>
  );
}
