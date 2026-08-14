import { motion } from 'framer-motion';

export default function CookieHealthCard({ 
  loadingCookies, 
  cookieStatus 
}) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel" 
      style={{ padding: '30px' }}
    >
      <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <i className="fa-solid fa-cookie-bite" style={{ color: 'var(--color-cyan)' }}></i> Parser Cookie Health
      </h3>

      {loadingCookies ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--color-text-secondary)' }}>
          <i className="fa-solid fa-spinner fa-spin"></i>
          <span>Polling directories...</span>
        </div>
      ) : cookieStatus ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          
          {/* Youtube cookies status */}
          <motion.div 
            whileHover={{ scale: 1.02 }}
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'rgba(255,255,255,0.01)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <span style={{ fontSize: '13px', fontWeight: '600', color: '#fff' }}>YouTube Cookies</span>
              <code style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>cookies/youtube.txt</code>
            </div>
            <span style={{ 
              fontSize: '10px', 
              fontWeight: '600', 
              padding: '4px 8px', 
              borderRadius: '4px',
              background: cookieStatus.youtube_cookies_exists ? 'rgba(46, 204, 113, 0.15)' : 'rgba(255, 0, 127, 0.15)',
              color: cookieStatus.youtube_cookies_exists ? '#2ecc71' : 'var(--color-pink)',
              border: cookieStatus.youtube_cookies_exists ? '1px solid #2ecc71' : '1px solid var(--color-pink)',
              boxShadow: cookieStatus.youtube_cookies_exists ? '0 0 10px rgba(46, 204, 113, 0.2)' : 'none'
            }}>
              {cookieStatus.youtube_cookies_exists ? 'DETECTED' : 'MISSING'}
            </span>
          </motion.div>

          {/* Instagram cookies status */}
          <motion.div 
            whileHover={{ scale: 1.02 }}
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'rgba(255,255,255,0.01)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <span style={{ fontSize: '13px', fontWeight: '600', color: '#fff' }}>Instagram Cookies</span>
              <code style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>cookies/insta.txt</code>
            </div>
            <span style={{ 
              fontSize: '10px', 
              fontWeight: '600', 
              padding: '4px 8px', 
              borderRadius: '4px',
              background: cookieStatus.instagram_cookies_exists ? 'rgba(46, 204, 113, 0.15)' : 'rgba(255, 0, 127, 0.15)',
              color: cookieStatus.instagram_cookies_exists ? '#2ecc71' : 'var(--color-pink)',
              border: cookieStatus.instagram_cookies_exists ? '1px solid #2ecc71' : '1px solid var(--color-pink)',
              boxShadow: cookieStatus.instagram_cookies_exists ? '0 0 10px rgba(46, 204, 113, 0.2)' : 'none'
            }}>
              {cookieStatus.instagram_cookies_exists ? 'DETECTED' : 'MISSING'}
            </span>
          </motion.div>

          {/* Fallback cookies status */}
          <motion.div 
            whileHover={{ scale: 1.02 }}
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'rgba(255,255,255,0.01)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <span style={{ fontSize: '13px', fontWeight: '600', color: '#fff' }}>Fallback Cookies</span>
              <code style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>cookies/fallback_cookies.txt</code>
            </div>
            <span style={{ 
              fontSize: '10px', 
              fontWeight: '600', 
              padding: '4px 8px', 
              borderRadius: '4px',
              background: cookieStatus.fallback_cookies_exists ? 'rgba(46, 204, 113, 0.15)' : 'rgba(255, 0, 127, 0.15)',
              color: cookieStatus.fallback_cookies_exists ? '#2ecc71' : 'var(--color-pink)',
              border: cookieStatus.fallback_cookies_exists ? '1px solid #2ecc71' : '1px solid var(--color-pink)',
              boxShadow: cookieStatus.fallback_cookies_exists ? '0 0 10px rgba(46, 204, 113, 0.2)' : 'none'
            }}>
              {cookieStatus.fallback_cookies_exists ? 'DETECTED' : 'MISSING'}
            </span>
          </motion.div>
        </div>
      ) : (
        <span style={{ color: 'var(--color-text-muted)' }}>Error loading cookie settings.</span>
      )}
    </motion.div>
  );
}
