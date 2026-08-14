import { motion, AnimatePresence } from 'framer-motion';
import { GlassButton } from '@/components/ui/UiloraModernButtons';

export default function DiagnosticsConsole({
  sandboxUrl,
  setSandboxUrl,
  extracting,
  extractedData,
  handleDiagnose
}) {
  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="glass-panel" 
      style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '20px' }}
    >
      <div>
        <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#fff', marginBottom: '4px' }}>
          Metadata Sandbox Diagnostic
        </h3>
        <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
          Perform test extractions and view raw JSON schemas returned by target parser engines.
        </p>
      </div>

      <form onSubmit={handleDiagnose} style={{ display: 'flex', gap: '12px' }}>
        <input 
          type="url"
          placeholder="Paste URL to extract (YouTube, Facebook, Vimeo, Rumble, etc...)"
          value={sandboxUrl}
          onChange={(e) => setSandboxUrl(e.target.value)}
          disabled={extracting}
          className="glow-input"
          style={{ flex: 1, padding: '12px 16px', fontSize: '14px' }}
          required
        />
        <GlassButton 
          type="submit"
          disabled={extracting}
          className="border-cyan-500/30 text-white font-semibold text-[12px] !py-[10px] !px-6 bg-transparent"
        >
          {extracting ? <i className="fa-solid fa-spinner fa-spin"></i> : 'Diagnose'}
        </GlassButton>
      </form>

      {/* Hacker-terminal style JSON output console */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)', fontWeight: '600' }}>
          Raw JSON Schema Output
        </span>

        {/* Custom shell layout */}
        <div className="glass-panel" style={{ overflow: 'hidden', border: '1px solid rgba(0, 242, 254, 0.15)', background: 'rgba(5, 4, 12, 0.98)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 15px', background: 'rgba(255, 255, 255, 0.02)', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
            <div style={{ display: 'flex', gap: '6px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ff5f56' }} />
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ffbd2e' }} />
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#27c93f' }} />
            </div>
            <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'rgba(0, 242, 254, 0.4)', letterSpacing: '0.5px' }}>
              schema_inspector.json
            </span>
            <div style={{ width: '30px' }} />
          </div>

          <div 
            className="hacker-terminal"
            style={{ 
              height: '380px', 
              border: 'none',
              boxShadow: 'none',
              fontSize: '12px',
              display: 'flex', 
              flexDirection: 'column', 
              justifyContent: extractedData ? 'flex-start' : 'center',
              alignItems: extractedData ? 'stretch' : 'center',
              background: 'transparent',
              color: '#00f2fe',
            }}
          >
            <AnimatePresence mode="wait">
              {extractedData ? (
                <motion.pre 
                  key="content"
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  style={{ margin: 0, overflow: 'auto', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)' }}
                >
                  {JSON.stringify(extractedData, null, 2)}
                </motion.pre>
              ) : (
                <motion.div 
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px', color: 'var(--color-text-muted)' }}
                >
                  <i className="fa-solid fa-bug-slash" style={{ fontSize: '20px' }}></i>
                  <span>Sandbox ready. Enter a URL to test parsing pipeline.</span>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
