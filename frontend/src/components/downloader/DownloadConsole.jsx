import { motion } from 'framer-motion';
import { GlassButton } from '@/components/ui/UiloraModernButtons';

export default function DownloadConsole({
  downloading,
  downloaded,
  fetchingQualities,
  qualities,
  selectedQuality,
  setSelectedQuality,
  downloadProgress,
  handleDownload
}) {
  return (
    <div className="glass-panel" style={{ padding: '24px', border: '1px solid rgba(0, 242, 254, 0.15)', background: 'rgba(0, 242, 254, 0.02)' }}>
      <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <i className="fa-solid fa-download" style={{ color: 'var(--color-cyan)' }}></i>Local Video Downloader
      </h4>
      
      {!downloading && !downloaded ? (
        <div style={{ display: 'flex', gap: '15px' }}>
          <select 
            value={selectedQuality}
            onChange={(e) => setSelectedQuality(e.target.value)}
            className="glow-input"
            disabled={fetchingQualities}
            style={{ flex: 1, padding: '10px 16px', fontSize: '14px', background: 'rgba(5, 4, 12, 0.8)' }}
          >
            {fetchingQualities ? (
              <option>Fetching formats...</option>
            ) : qualities.length > 0 ? (
              qualities.map((q) => (
                <option key={q.format_id} value={q.format_id}>
                  {q.height}p ({q.ext.toUpperCase()}) - {q.filesize}
                </option>
              ))
            ) : (
              <option value="best">Best Quality (Auto)</option>
            )}
          </select>
          <GlassButton 
            text="DOWNLOAD" 
            onClick={handleDownload}
            className="min-w-[130px] !py-[10px] text-[11px] font-bold border-cyan-500/30 hover:border-cyan-500/60"
          />
        </div>
      ) : downloading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--color-text-secondary)' }}>
            <span>Downloading to Local Storage...</span>
            <span style={{ fontFamily: 'var(--font-mono)' }}>
              {downloadProgress?.speed || '0 B/s'} | {downloadProgress?.eta || 'calculating...'}
            </span>
          </div>
          
          {/* Progress bar container */}
          <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden', position: 'relative' }}>
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${downloadProgress?.progress || 0}%` }}
              transition={{ duration: 0.1 }}
              style={{
                height: '100%',
                background: 'linear-gradient(to right, var(--color-cyan), var(--color-purple))',
                boxShadow: 'var(--neon-shadow-cyan)',
              }}
            />
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', textAlign: 'right' }}>
            {downloadProgress?.downloaded} / {downloadProgress?.total} ({Math.round(downloadProgress?.progress || 0)}%)
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#2ecc71', fontWeight: '600', fontSize: '14px' }}>
            <i className="fa-solid fa-circle-check"></i>
            <span>Download completed! Local file stored.</span>
          </div>
          <button 
            disabled 
            className="btn-cyber" 
            style={{
              background: 'rgba(46, 204, 113, 0.2)',
              border: '1px solid #2ecc71',
              color: '#2ecc71',
              padding: '8px 20px',
              fontSize: '13px'
            }}
          >
            Downloaded ✓
          </button>
        </div>
      )}
    </div>
  );
}
