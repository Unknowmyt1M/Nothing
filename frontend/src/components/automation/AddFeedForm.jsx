import { motion, AnimatePresence } from 'framer-motion';
import { GlassButton } from '@/components/ui/UiloraModernButtons';

export default function AddFeedForm({
  channelUrl,
  setChannelUrl,
  analyzingUrl,
  analyzedChannel,
  handleAnalyze,
  handleAddChannel
}) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="glass-panel" 
      style={{ padding: '30px' }}
    >
      <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <i className="fa-solid fa-folder-plus" style={{ color: 'var(--color-cyan)' }}></i> Add Monitored YouTube Feed
      </h3>
      <form onSubmit={handleAnalyze} style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
        <input
          type="url"
          placeholder="Paste YouTube channel URL (e.g., https://youtube.com/@techchannel)"
          value={channelUrl}
          onChange={(e) => setChannelUrl(e.target.value)}
          disabled={analyzingUrl}
          className="glow-input"
          style={{ flex: 1, padding: '12px 16px', fontSize: '14px' }}
          required
        />
        <GlassButton
          type="submit"
          disabled={analyzingUrl}
          className="border-cyan-500/30 text-white font-semibold text-[12px] !py-[10px] !px-6 bg-transparent"
        >
          {analyzingUrl ? <i className="fa-solid fa-circle-notch fa-spin"></i> : 'Analyze'}
        </GlassButton>
      </form>

      {/* Analyzed Channel confirmation Card */}
      <AnimatePresence>
        {analyzedChannel && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className="glass-panel" 
            style={{ padding: '20px', border: '1px solid rgba(0, 242, 254, 0.2)', background: 'rgba(0, 242, 254, 0.02)', display: 'flex', flexDirection: 'column', gap: '15px' }}
          >
            <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
              <img
                src={analyzedChannel.logo_url}
                alt="Channel Logo"
                style={{ width: '48px', height: '48px', borderRadius: '50%', border: '1px solid var(--color-border)' }}
              />
              <div style={{ flex: 1 }}>
                <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#fff' }}>{analyzedChannel.name}</h4>
                <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                  {analyzedChannel.subscriber_count} | {analyzedChannel.total_videos} videos
                </span>
              </div>
            </div>
            <GlassButton
              onClick={handleAddChannel}
              className="w-full !py-3.5 font-bold tracking-wider text-[11px] border-cyan-500/30 hover:border-cyan-500/60"
            >
              Confirm Monitor Registration
            </GlassButton>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
