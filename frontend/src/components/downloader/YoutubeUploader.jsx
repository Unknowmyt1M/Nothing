import { motion, AnimatePresence } from 'framer-motion';
import { GlassButton } from '@/components/ui/UiloraModernButtons';

export default function YoutubeUploader({
  downloaded,
  uploading,
  uploaded,
  privacy,
  setPrivacy,
  uploadProgress,
  youtubeUrl,
  handleUpload
}) {
  return (
    <AnimatePresence>
      {downloaded && (
        <motion.div 
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel" 
          style={{ padding: '24px', border: '1px solid rgba(255, 0, 127, 0.15)', background: 'rgba(255, 0, 127, 0.01)' }}
        >
          <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <i className="fa-brands fa-youtube" style={{ color: 'var(--color-pink)' }}></i>YouTube Auto-Uploader
          </h4>

          {!uploading && !uploaded ? (
            <div style={{ display: 'flex', gap: '15px' }}>
              <select 
                value={privacy}
                onChange={(e) => setPrivacy(e.target.value)}
                className="glow-input"
                style={{ flex: 1, padding: '10px 16px', fontSize: '14px', background: 'rgba(5, 4, 12, 0.8)' }}
              >
                <option value="public">Public - Publish immediately</option>
                <option value="unlisted">Unlisted - Access via direct link</option>
                <option value="private">Private - Access restricted to owner</option>
              </select>
              <GlassButton 
                onClick={handleUpload}
                className="min-w-[150px] !py-[12px] text-[11px] font-bold border-pink-500/30 hover:border-pink-500/60"
              >
                Publish
              </GlassButton>
            </div>
          ) : uploading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--color-text-secondary)' }}>
                <span>Uploading to YouTube server...</span>
                <span style={{ fontFamily: 'var(--font-mono)' }}>
                  {uploadProgress?.upload_speed || '0 B/s'} | {uploadProgress?.upload_eta || 'calculating...'}
                </span>
              </div>
              <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${uploadProgress?.progress || 0}%` }}
                  transition={{ duration: 0.1 }}
                  style={{
                    height: '100%',
                    background: 'linear-gradient(to right, var(--color-pink), var(--color-purple))',
                    boxShadow: 'var(--neon-shadow-pink)',
                  }}
                />
              </div>
              <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', textAlign: 'right' }}>
                {uploadProgress?.uploaded} / {uploadProgress?.total_upload} ({Math.round(uploadProgress?.progress || 0)}%)
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', alignItems: 'center', textAlign: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-cyan)', fontWeight: '600', fontSize: '15px' }}>
                <i className="fa-solid fa-circle-check"></i>
                <span>Video published on YouTube channel!</span>
              </div>
              <GlassButton
                onClick={() => window.open(youtubeUrl, '_blank')}
                className="border-red-500/30 text-white font-bold tracking-widest text-[12px] hover:border-red-400 min-w-[200px] !py-[12px]"
              >
                <i className="fa-brands fa-youtube mr-2" style={{ color: '#ff0000', fontSize: '16px' }}></i>
                <span>WATCH ON YOUTUBE</span>
              </GlassButton>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
