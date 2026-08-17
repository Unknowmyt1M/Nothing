import { motion } from 'framer-motion';

export default function MetadataCard({ 
  metadata, 
  setMetadata, 
  triggerToast,
  children 
}) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 30, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 30, scale: 0.97 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      className="glass-panel metadata-grid"
      style={{ padding: '35px' }}
    >
      {/* Left Column: Thumbnail and stats */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ position: 'relative', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--color-border)', boxShadow: '0 5px 15px rgba(0,0,0,0.5)' }}>
          <img 
            src={metadata.thumbnail || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=600'} 
            alt="Video Thumbnail"
            style={{ width: '100%', display: 'block', objectFit: 'cover', height: '170px' }}
          />
          <span className={`platform-badge ${metadata.platform}`} style={{ position: 'absolute', top: '12px', left: '12px' }}>
            {metadata.platform}
          </span>
        </div>

        {/* Stats list */}
        <div className="glass-panel" style={{ padding: '20px', background: 'rgba(255, 255, 255, 0.02)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <h4 style={{ fontSize: '13px', color: 'var(--color-cyan)', fontWeight: '600', letterSpacing: '1px', textTransform: 'uppercase', marginBottom: '5px' }}>
            <i className="fa-solid fa-chart-simple me-2"></i>Statistics
          </h4>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px' }}>
            <span style={{ color: 'var(--color-text-secondary)', flex: 1 }}>Duration:</span>
            <strong style={{ fontFamily: 'var(--font-mono)' }}>{metadata.duration}</strong>
          </div>
          {metadata.uploader && (
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px' }}>
              <span style={{ color: 'var(--color-text-secondary)', flex: 1 }}>Creator:</span>
              <strong style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '120px' }}>{metadata.uploader}</strong>
            </div>
          )}
          {metadata.view_count && (
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px' }}>
              <span style={{ color: 'var(--color-text-secondary)', flex: 1 }}>Views:</span>
              <strong>{metadata.view_count}</strong>
            </div>
          )}
          {metadata.upload_date && (
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px' }}>
              <span style={{ color: 'var(--color-text-secondary)', flex: 1 }}>Date:</span>
              <strong>{metadata.upload_date}</strong>
            </div>
          )}
        </div>

        {/* Tech details (Codecs, etc) */}
        {(metadata.video_codec || metadata.quality) && (
          <div className="glass-panel" style={{ padding: '20px', background: 'rgba(255, 255, 255, 0.02)', display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
            <h4 style={{ fontSize: '13px', color: 'var(--color-cyan)', fontWeight: '600', letterSpacing: '1px', textTransform: 'uppercase', marginBottom: '5px' }}>
              <i className="fa-solid fa-microchip me-2"></i>Technical Specs
            </h4>
            {metadata.quality && <div><span style={{ color: 'var(--color-text-secondary)' }}>Resolution:</span> <code style={{ color: '#fff', float: 'right' }}>{metadata.quality}</code></div>}
            {metadata.video_codec && <div><span style={{ color: 'var(--color-text-secondary)' }}>Video Codec:</span> <code style={{ color: '#fff', float: 'right' }}>{metadata.video_codec}</code></div>}
            {metadata.audio_codec && <div><span style={{ color: 'var(--color-text-secondary)' }}>Audio Codec:</span> <code style={{ color: '#fff', float: 'right' }}>{metadata.audio_codec}</code></div>}
            {metadata.fps && <div><span style={{ color: 'var(--color-text-secondary)' }}>Frame Rate:</span> <code style={{ color: '#fff', float: 'right' }}>{metadata.fps}</code></div>}
            {metadata.file_size && <div><span style={{ color: 'var(--color-text-secondary)' }}>File Size:</span> <code style={{ color: '#fff', float: 'right' }}>{metadata.file_size}</code></div>}
          </div>
        )}
      </div>

      {/* Right Column: Title/Desc editors & action consoles */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
        {/* Title block */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{ fontSize: '13px', color: 'var(--color-text-secondary)', fontWeight: '600' }}>Video Title</label>
          <input 
            type="text" 
            value={metadata.title}
            onChange={(e) => setMetadata({ ...metadata, title: e.target.value })}
            className="glow-input"
            style={{ padding: '12px 16px', fontSize: '14px', width: '100%' }}
          />
        </div>

        {/* Description block */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{ fontSize: '13px', color: 'var(--color-text-secondary)', fontWeight: '600' }}>Description</label>
          <textarea 
            value={metadata.description}
            onChange={(e) => setMetadata({ ...metadata, description: e.target.value })}
            className="glow-input"
            rows="4"
            style={{ padding: '12px 16px', fontSize: '13px', width: '100%', resize: 'none', fontFamily: 'var(--font-sans)' }}
          />
        </div>

        {/* Clickable Tags */}
        {metadata.tags && metadata.tags.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '13px', color: 'var(--color-text-secondary)', fontWeight: '600' }}>Extracted Tags</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', maxHeight: '100px', overflowY: 'auto', padding: '5px 0' }}>
              {metadata.tags.map((tag, idx) => (
                <motion.span 
                  key={idx} 
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    navigator.clipboard.writeText(tag);
                    triggerToast(`Copied: ${tag}`, 'success');
                  }}
                  style={{
                    padding: '4px 10px',
                    fontSize: '11px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid var(--color-border)',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    transition: 'border-color 0.2s ease, color 0.2s ease',
                    color: 'var(--color-text-secondary)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--color-cyan)';
                    e.currentTarget.style.color = '#ffffff';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--color-border)';
                    e.currentTarget.style.color = 'var(--color-text-secondary)';
                  }}
                >
                  #{tag}
                </motion.span>
              ))}
            </div>
          </div>
        )}

        {/* Render child components (DownloadConsole and YoutubeUploader panels) */}
        {children}
      </div>
    </motion.div>
  );
}
