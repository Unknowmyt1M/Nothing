import { motion, AnimatePresence } from 'framer-motion';
import { GlassButton } from '@/components/ui/UiloraModernButtons';

export default function AdvancedSettingsForm({
  authStatus,
  apiKey,
  setApiKey,
  monitorInterval,
  setMonitorInterval,
  savingSettings,
  showApiKey,
  setShowApiKey,
  handleSaveSettings
}) {
  return (
    <AnimatePresence>
      {authStatus.authenticated && (
        <motion.div 
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel" 
          style={{ padding: '35px' }}
        >
          <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '25px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <i className="fa-solid fa-screwdriver-wrench" style={{ color: 'var(--color-cyan)' }}></i> Advanced Console Settings
          </h3>
          
          <form onSubmit={handleSaveSettings} style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
            
            {/* YouTube API Key */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label style={{ fontSize: '14px', fontWeight: '600', color: 'var(--color-text-secondary)' }}>
                  YouTube Data API v3 Key
                </label>
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--color-cyan)',
                    fontSize: '12px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px'
                  }}
                >
                  <i className={`fa-solid ${showApiKey ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                  <span>{showApiKey ? 'Hide Key' : 'Reveal'}</span>
                </button>
              </div>
              <input
                type={showApiKey ? 'text' : 'password'}
                placeholder="Enter Google Developer API Key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="glow-input"
                style={{ padding: '14px 16px', fontSize: '14px', width: '100%' }}
              />
              <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                API keys are used in background tasks to scan channel playlists and download feeds without hitting rate-limits.
              </span>
            </div>

            {/* Automation Scan Cooldown Interval */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '14px', fontWeight: '600', color: 'var(--color-text-secondary)' }}>
                Auto Monitor Scan Cooldown (seconds)
              </label>
              <input
                type="number"
                min="10"
                placeholder="e.g. 300"
                value={monitorInterval}
                onChange={(e) => setMonitorInterval(e.target.value)}
                className="glow-input"
                style={{ padding: '14px 16px', fontSize: '14px', width: '100%' }}
                required
              />
              <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                Minimum interval is 10 seconds. We recommend at least 300 seconds (5 minutes) to conserve API quotas.
              </span>
            </div>

            {/* Submit button */}
            <div style={{ display: 'flex' }}>
              <GlassButton
                type="submit"
                disabled={savingSettings}
                className="min-w-[160px] !py-[12px] font-bold text-[12px] tracking-widest uppercase disabled:opacity-50 border-cyan-500/30 hover:border-cyan-500/60"
              >
                {savingSettings ? (
                  <span className="flex items-center justify-center gap-2">
                    <i className="fa-solid fa-circle-notch fa-spin"></i> Saving...
                  </span>
                ) : (
                  'Save Changes'
                )}
              </GlassButton>
            </div>

          </form>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
