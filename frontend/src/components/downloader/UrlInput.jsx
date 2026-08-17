import { motion, AnimatePresence } from 'framer-motion';
import { GlassButton } from '@/components/ui/UiloraModernButtons';

export default function UrlInput({ 
  url, 
  setUrl, 
  platformInfo, 
  extracting, 
  handleExtract 
}) {
  const getPlatformIcon = (platform) => {
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
    return icons[platform] || 'fa-solid fa-globe';
  };

  return (
    <div className={`glass-panel scanner-container ${extracting ? 'scanning' : ''}`} style={{ padding: '30px', marginBottom: '30px', position: 'relative' }}>
      {extracting && <div className="scanner-laser"></div>}
      <form onSubmit={handleExtract} className="url-form">
        <div className="url-form-input">
          <span style={{ position: 'absolute', left: '16px', color: 'var(--color-cyan)', fontSize: '18px', zIndex: 1 }}>
            <i className={getPlatformIcon(platformInfo.platform)}></i>
          </span>
          <input 
            type="url" 
            placeholder="Paste link here (YouTube, Instagram, TikTok, Facebook, Rumble, etc...)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={extracting}
            className="glow-input"
            style={{
              width: '100%',
              padding: '16px 20px 16px 50px',
              fontSize: '15px',
              letterSpacing: '0.5px'
            }}
            required
          />
        </div>
        <GlassButton 
          type="submit" 
          disabled={extracting}
          className="url-form-btn border-cyan-500/30 text-white font-bold tracking-widest text-[12px] hover:border-cyan-400 !py-[13px]"
        >
          {extracting ? <i className="fa-solid fa-circle-notch fa-spin mr-2"></i> : 'EXTRACT'}
        </GlassButton>
      </form>

      {/* Live platform status detection info */}
      <AnimatePresence>
        {platformInfo.platform !== 'unknown' && (
          <motion.div 
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '15px', fontSize: '13px' }}
          >
            <i className={`fa-solid ${platformInfo.supported ? 'fa-circle-check' : 'fa-circle-xmark'}`} style={{ color: platformInfo.supported ? '#2ecc71' : 'var(--color-pink)' }}></i>
            <span style={{ color: 'var(--color-text-secondary)' }}>
              Detected Platform: <strong style={{ color: '#ffffff' }}>{platformInfo.display_name}</strong> 
              {platformInfo.supported ? (
                <span style={{ color: '#2ecc71', marginLeft: '5px' }}>(Supported ✓)</span>
              ) : (
                <span style={{ color: 'var(--color-pink)', marginLeft: '5px' }}>(Coming Soon)</span>
              )}
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
