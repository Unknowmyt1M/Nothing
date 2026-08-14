import { motion, AnimatePresence } from 'framer-motion';

export default function SupportedPlatformsGrid({
  loading,
  search,
  setSearch,
  filteredPlatforms
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

  const getPlatformClass = (id) => {
    const classes = {
      'youtube': 'youtube',
      'instagram': 'instagram',
      'facebook': 'facebook',
      'twitter': 'twitter',
      'vimeo': 'vimeo',
      'rumble': 'rumble',
      'direct_url': 'direct_url'
    };
    return classes[id] || 'tiktok';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Search filter bar */}
      <motion.div 
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel" 
        style={{ padding: '15px 20px', display: 'flex', alignItems: 'center', gap: '15px' }}
      >
        <i className="fa-solid fa-magnifying-glass" style={{ color: 'var(--color-cyan)', fontSize: '16px' }}></i>
        <input 
          type="text"
          placeholder="Search supported platforms..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="glow-input"
          style={{ flex: 1, padding: '10px 15px', border: 'none', background: 'transparent', outline: 'none' }}
        />
      </motion.div>

      {loading ? (
        <div className="glass-panel" style={{ padding: '50px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '15px' }}>
          <i className="fa-solid fa-circle-notch fa-spin" style={{ color: 'var(--color-cyan)', fontSize: '24px' }}></i>
          <span style={{ color: 'var(--color-text-secondary)' }}>Querying parser specs...</span>
        </div>
      ) : filteredPlatforms.length === 0 ? (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
          No matching platforms found.
        </div>
      ) : (
        <motion.div 
          layout
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}
        >
          <AnimatePresence>
            {filteredPlatforms.map((p, idx) => (
              <motion.div 
                key={p.id} 
                layout
                initial={{ opacity: 0, scale: 0.95, y: 15 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 15 }}
                transition={{ type: 'spring', stiffness: 300, damping: 25, delay: Math.min(idx * 0.03, 0.3) }}
                whileHover={{ scale: 1.02, borderColor: 'rgba(0, 242, 254, 0.25)' }}
                className="glass-panel" 
                style={{ 
                  padding: '24px', 
                  display: 'flex', 
                  flexDirection: 'column', 
                  gap: '15px',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                {/* Decorative glowing back orb */}
                <div style={{
                  position: 'absolute',
                  top: '-20px',
                  right: '-20px',
                  width: '60px',
                  height: '60px',
                  borderRadius: '50%',
                  background: 'var(--color-cyan)',
                  filter: 'blur(30px)',
                  opacity: 0.1,
                  pointerEvents: 'none'
                }}></div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '8px',
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid var(--color-border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <i className={getPlatformIcon(p.id)} style={{ fontSize: '20px', color: '#fff' }}></i>
                  </div>
                  <div>
                    <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#fff' }}>{p.name}</h4>
                    <span className={`platform-badge ${getPlatformClass(p.id)}`} style={{ fontSize: '8px', padding: '2px 6px' }}>
                      ACTIVE
                    </span>
                  </div>
                </div>

                <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', lineHeight: '1.5', flex: 1 }}>
                  {p.description || `Extract and download content directly from ${p.name} using the UpDownVid framework.`}
                </p>

                <div style={{ 
                  display: 'flex', 
                  gap: '8px', 
                  paddingTop: '10px', 
                  borderTop: '1px solid var(--color-border)', 
                  fontSize: '11px', 
                  color: 'var(--color-text-muted)' 
                }}>
                  <span><i className="fa-solid fa-circle-check" style={{ color: '#2ecc71', marginRight: '4px' }}></i>Video</span>
                  <span><i className="fa-solid fa-circle-check" style={{ color: '#2ecc71', marginRight: '4px' }}></i>Audio</span>
                  <span><i className="fa-solid fa-circle-check" style={{ color: '#2ecc71', marginRight: '4px' }}></i>High-Res</span>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      )}
    </div>
  );
}
