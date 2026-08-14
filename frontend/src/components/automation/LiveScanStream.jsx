import { motion, AnimatePresence } from 'framer-motion';
import { GlassButton } from '@/components/ui/UiloraModernButtons';

export default function LiveScanStream({
  logs,
  clearingLogs,
  handleClearLogs,
  terminalEndRef
}) {
  const getLogClass = (type) => {
    if (type === 'success') return 'terminal-line success';
    if (type === 'error') return 'terminal-line error';
    if (type === 'warning') return 'terminal-line warning';
    return 'terminal-line';
  };

  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      style={{ display: 'flex', flexDirection: 'column', gap: '20px', height: '100%' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '16px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <i className="fa-solid fa-terminal" style={{ color: '#39ff14' }}></i> Live Scan Stream
        </h3>
        
        <GlassButton
          onClick={handleClearLogs}
          disabled={clearingLogs || logs.length === 0}
          className="!py-2 !px-4 text-[11px] rounded-lg disabled:opacity-30 disabled:pointer-events-none border-red-500/20 text-red-400 hover:border-red-500/50 hover:text-white"
        >
          <span className="flex items-center gap-1.5">
            {clearingLogs ? <i className="fa-solid fa-spinner fa-spin"></i> : <i className="fa-solid fa-circle-minus"></i>}
            Clear Console
          </span>
        </GlassButton>
      </div>

      {/* Premium Terminal window wraps console */}
      <div className="glass-panel" style={{ overflow: 'hidden', border: '1px solid rgba(57, 255, 20, 0.15)', background: 'rgba(5, 4, 12, 0.95)' }}>
        {/* Terminal Window Header Bar */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 18px', background: 'rgba(255, 255, 255, 0.02)', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
          <div style={{ display: 'flex', gap: '6px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ff5f56' }} />
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ffbd2e' }} />
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#27c93f' }} />
          </div>
          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'rgba(255,255,255,0.4)', letterSpacing: '1px' }}>
            MONITOR_STREAM.SH
          </span>
          <div style={{ width: '38px' }} />
        </div>

        <div 
          className="hacker-terminal" 
          style={{ 
            height: '610px', 
            border: 'none',
            boxShadow: 'none',
            background: 'transparent',
            display: 'flex', 
            flexDirection: 'column', 
            justifyContent: logs.length === 0 ? 'center' : 'flex-start',
            alignItems: logs.length === 0 ? 'center' : 'stretch'
          }}
        >
          {logs.length === 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px', color: '#636e72', fontSize: '14px' }}>
              <i className="fa-solid fa-ban" style={{ fontSize: '24px' }}></i>
              <span>Console active. Awaiting scanning triggers...</span>
            </div>
          ) : (
            <>
              {logs.map((log, idx) => (
                <motion.div 
                  key={idx} 
                  initial={{ opacity: 0, x: -5 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={getLogClass(log.type)}
                >
                  {log.message}
                </motion.div>
              ))}
              <div ref={terminalEndRef} />
            </>
          )}
        </div>
      </div>
    </motion.div>
  );
}
