import { motion, AnimatePresence } from 'framer-motion';

export default function MonitoredFeedsList({
  loadingChannels,
  channels,
  handleRemoveChannel
}) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="glass-panel" 
      style={{ padding: '30px' }}
    >
      <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <i className="fa-solid fa-list-check" style={{ color: 'var(--color-cyan)' }}></i> Monitored Feeds ({channels.length})
      </h3>

      {loadingChannels ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--color-text-secondary)', padding: '20px' }}>
          <i className="fa-solid fa-circle-notch fa-spin"></i>
          <span>Loading active channels...</span>
        </div>
      ) : channels.length === 0 ? (
        <p style={{ color: 'var(--color-text-muted)', fontSize: '14px', fontStyle: 'italic', padding: '10px' }}>
          No YouTube channels configured for monitoring yet. Add one above!
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <AnimatePresence initial={false}>
            {channels.map((channel) => (
              <motion.div
                key={channel.channel_id}
                layout
                initial={{ opacity: 0, height: 0, scale: 0.95 }}
                animate={{ opacity: 1, height: 'auto', scale: 1 }}
                exit={{ opacity: 0, height: 0, scale: 0.95, transition: { duration: 0.2 } }}
                transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                style={{ overflow: 'hidden' }}
              >
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '15px',
                  padding: '15px',
                  borderRadius: '10px',
                  background: 'rgba(255, 255, 255, 0.01)',
                  border: '1px solid var(--color-border)',
                  position: 'relative'
                }}>
                  <img
                    src={channel.logo_url}
                    alt="Channel logo"
                    style={{ width: '40px', height: '40px', borderRadius: '50%' }}
                  />
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#fff', textOverflow: 'ellipsis', whiteSpace: 'nowrap', overflow: 'hidden' }}>
                      {channel.name}
                    </h4>
                    <p style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                      Last Scan: {channel.last_checked ? new Date(channel.last_checked * 1000).toLocaleTimeString() : 'Never'} | Quality: {channel.quality || '1080p'}
                    </p>
                  </div>

                  <button
                    onClick={() => handleRemoveChannel(channel.channel_id, channel.name)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--color-text-muted)',
                      cursor: 'pointer',
                      padding: '8px',
                      fontSize: '16px',
                      transition: 'color 0.2s ease'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.color = 'var(--color-pink)'}
                    onMouseLeave={(e) => e.currentTarget.style.color = 'var(--color-text-muted)'}
                  >
                    <i className="fa-solid fa-trash-can"></i>
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  );
}
