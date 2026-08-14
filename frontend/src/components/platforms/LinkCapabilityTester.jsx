import { motion, AnimatePresence } from 'framer-motion';
import { GlassButton } from '@/components/ui/UiloraModernButtons';

export default function LinkCapabilityTester({
  testUrl,
  setTestUrl,
  testing,
  testResult,
  handleTestUrl
}) {
  const getPlatformIcon = (id) => {
    const icons = {
      'youtube': 'fa-brands fa-youtube',
      'instagram': 'fa-brands fa-instagram',
      'facebook': 'fa-brands fa-facebook',
      'twitter': 'fa-brands fa-x-twitter',
      'tiktok': 'fa-brands fa-tiktok',
      'vimeo': 'fa-brands fa-vimeo',
      'reddit': 'fa-brands fa-reddit-alien',
      'twitch': 'fa-brands fa-twitch',
      'rumble': 'fa-solid fa-video',
      'direct_url': 'fa-solid fa-link'
    };
    return icons[id] || 'fa-solid fa-globe';
  };

  return (
    <div className={`glass-panel scanner-container ${testing ? 'scanning' : ''}`} style={{ padding: '30px', position: 'relative' }}>
      {testing && <div className="scanner-laser"></div>}
      <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <i className="fa-solid fa-wand-magic-sparkles" style={{ color: 'var(--color-cyan)' }}></i> Link Capability Tester
      </h3>
      <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '20px', lineHeight: '1.5' }}>
        Paste any social media or stream link below to test if our parser script can analyze it.
      </p>

      <form onSubmit={handleTestUrl} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        <input 
          type="url"
          placeholder="Paste URL to test (e.g. https://...)"
          value={testUrl}
          onChange={(e) => setTestUrl(e.target.value)}
          disabled={testing}
          className="glow-input"
          style={{ padding: '12px 15px', fontSize: '14px', width: '100%' }}
          required
        />
        <GlassButton
          type="submit"
          disabled={testing}
          className="w-full !py-3.5 font-bold tracking-wider text-[11px] border-cyan-500/30 hover:border-cyan-500/60"
        >
          {testing ? <i className="fa-solid fa-circle-notch fa-spin"></i> : 'Test URL'}
        </GlassButton>
      </form>

      {/* Test Result output */}
      <AnimatePresence>
        {testResult && (
          <motion.div 
            initial={{ opacity: 0, height: 0, scale: 0.95 }}
            animate={{ opacity: 1, height: 'auto', scale: 1 }}
            exit={{ opacity: 0, height: 0, scale: 0.95 }}
            style={{ 
              marginTop: '25px', 
              padding: '20px', 
              borderRadius: '10px', 
              background: 'rgba(255,255,255,0.01)', 
              border: '1px solid var(--color-border)',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              overflow: 'hidden'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Status:</span>
              <span style={{ 
                fontSize: '11px', 
                fontWeight: '600', 
                color: testResult.supported ? '#2ecc71' : 'var(--color-pink)' 
              }}>
                {testResult.supported ? 'SUPPORTED' : 'UNSUPPORTED'}
              </span>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Platform:</span>
              <span style={{ fontSize: '13px', fontWeight: '700', color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <i className={getPlatformIcon(testResult.platform)} style={{ color: 'var(--color-cyan)' }}></i>
                {testResult.display_name}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '11px', color: 'var(--color-text-muted)', borderTop: '1px solid var(--color-border)', paddingTop: '10px' }}>
              <span>Target Parser Module:</span>
              <code style={{ color: 'var(--color-cyan)', fontSize: '11px' }}>
                backend/platforms/{testResult.platform}.py
              </code>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
