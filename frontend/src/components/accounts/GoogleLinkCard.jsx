import { motion, AnimatePresence } from 'framer-motion';
import { GlassButton } from '@/components/ui/UiloraModernButtons';

export default function GoogleLinkCard({ 
  authStatus, 
  handleConnect, 
  handleDisconnect 
}) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel" 
      style={{ padding: '35px' }}
    >
      <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <i className="fa-brands fa-google" style={{ color: 'var(--color-cyan)' }}></i> Google Services Link
      </h3>

      {!authStatus.authenticated ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px', lineHeight: '1.6' }}>
            To unlock the direct publishing features, you need to sync your YouTube channel. Connecting will grant UpDownVid the permission to upload processed videos on your behalf.
          </p>
          <div style={{ display: 'flex' }}>
            <GlassButton
              onClick={handleConnect}
              className="!px-8 !py-4 font-semibold tracking-wider text-[12px] border-cyan-500/30 hover:border-cyan-500/60"
            >
              <i className="fa-brands fa-google-play mr-2"></i> Sync Google Account
            </GlassButton>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
          {/* Linked Profile details */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px', background: 'rgba(255,255,255,0.02)', padding: '20px', borderRadius: '12px', border: '1px solid var(--color-border)' }}>
            <motion.div whileHover={{ scale: 1.05 }}>
              <img 
                src={authStatus.user?.picture || 'https://www.gravatar.com/avatar?d=mp'} 
                alt="Profile Avatar"
                onError={(e) => { e.target.src = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 60 60"><rect width="60" height="60" rx="30" fill="%2312101f"/><text x="30" y="38" text-anchor="middle" fill="%2300f2fe" font-size="24" font-family="sans-serif">U</text></svg>'); }}
                style={{ width: '60px', height: '60px', borderRadius: '50%', border: '2px solid var(--color-cyan)', boxShadow: 'var(--neon-shadow-cyan)' }}
              />
            </motion.div>
            <div style={{ flex: 1 }}>
              <h4 style={{ fontSize: '16px', fontWeight: '700', color: '#ffffff' }}>{authStatus.user?.name}</h4>
              <span style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>{authStatus.user?.email}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <span style={{ 
                fontSize: '11px', 
                background: 'rgba(46, 204, 113, 0.15)', 
                border: '1px solid #2ecc71', 
                color: '#2ecc71', 
                padding: '5px 12px', 
                borderRadius: '20px',
                textAlign: 'center',
                fontWeight: '600'
              }}>
                CONNECTED
              </span>
              <GlassButton 
                onClick={handleDisconnect}
                className="border-pink-500/20 text-pink-500 hover:border-pink-500/50 hover:text-white !px-4 !py-2 text-[12px] rounded-lg bg-transparent"
              >
                Disconnect
              </GlassButton>
            </div>
          </div>

          {/* YouTube Channel Stats block */}
          <AnimatePresence>
            {authStatus.youtube_channel ? (
              <motion.div 
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-panel" 
                style={{ padding: '25px', background: 'rgba(255, 0, 127, 0.02)', border: '1px solid rgba(255, 0, 127, 0.15)' }}
              >
                <h4 style={{ fontSize: '14px', fontWeight: '600', color: 'var(--color-pink)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '15px' }}>
                  <i className="fa-brands fa-youtube me-2"></i>Linked YouTube Channel
                </h4>
                <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                  <img 
                    src={authStatus.youtube_channel?.snippet?.thumbnails?.high?.url || 'https://yt3.ggpht.com/a/default-user=s800-c-k-c0x00ffffff-no-rj'} 
                    alt="Channel Thumbnail"
                    style={{ width: '50px', height: '50px', borderRadius: '50%', border: '1px solid var(--color-border)' }}
                  />
                  <div style={{ flex: 1 }}>
                    <h5 style={{ fontSize: '15px', fontWeight: '700', color: '#fff' }}>
                      {authStatus.youtube_channel?.snippet?.title}
                    </h5>
                    <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 1, WebkitBoxOrient: 'vertical' }}>
                      {authStatus.youtube_channel?.snippet?.description || 'No description available'}
                    </p>
                  </div>
                  
                  {/* Sub/Video counts */}
                  <div style={{ display: 'flex', gap: '20px' }}>
                    <div style={{ textAlign: 'center' }}>
                      <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Subscribers</span>
                      <p style={{ fontSize: '15px', fontWeight: '700', color: 'var(--color-cyan)' }}>
                        {authStatus.youtube_channel?.statistics?.subscriberCount ? 
                          parseInt(authStatus.youtube_channel.statistics.subscriberCount).toLocaleString() : 0}
                      </p>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Total Videos</span>
                      <p style={{ fontSize: '15px', fontWeight: '700', color: '#ffffff' }}>
                        {authStatus.youtube_channel?.statistics?.videoCount ? 
                          parseInt(authStatus.youtube_channel.statistics.videoCount).toLocaleString() : 0}
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(255,255,255,0.01)', padding: '15px 20px', borderRadius: '8px', border: '1px solid var(--color-border)', fontSize: '13px' }}
              >
                <i className="fa-solid fa-circle-info" style={{ color: 'var(--color-cyan)' }}></i>
                <span style={{ color: 'var(--color-text-secondary)' }}>No YouTube channel profile detected on linked account. Direct uploads may fail.</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  );
}
