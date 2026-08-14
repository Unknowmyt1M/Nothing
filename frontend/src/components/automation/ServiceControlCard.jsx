import { motion } from 'framer-motion';
import { GlassButton } from '@/components/ui/UiloraModernButtons';

export default function ServiceControlCard({ 
  serviceActive, 
  togglingService, 
  handleToggleService 
}) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel" 
      style={{ padding: '25px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '20px' }}
    >
      <div>
        <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#fff', marginBottom: '4px' }}>
          Monitoring Pipeline Service
        </h3>
        <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
          Runs background workers looking for feed updates.
        </p>
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
        <span style={{
          fontSize: '11px',
          fontWeight: '700',
          letterSpacing: '1px',
          padding: '6px 12px',
          borderRadius: '6px',
          background: serviceActive ? 'rgba(57, 255, 20, 0.1)' : 'rgba(255, 0, 127, 0.1)',
          border: serviceActive ? '1px solid #39ff14' : '1px solid var(--color-pink)',
          color: serviceActive ? '#39ff14' : 'var(--color-pink)',
          boxShadow: serviceActive ? '0 0 10px rgba(57, 255, 20, 0.2)' : 'none'
        }}>
          {serviceActive ? 'ACTIVE ⚡' : 'STOPPED 🛑'}
        </span>

        {serviceActive ? (
          <GlassButton
            onClick={handleToggleService}
            disabled={togglingService}
            className="border-pink-500/20 text-pink-500 hover:border-pink-500/50 hover:text-white !py-2 !px-5 text-[12px] rounded-lg bg-transparent"
          >
            {togglingService ? <i className="fa-solid fa-spinner fa-spin"></i> : 'Stop Service'}
          </GlassButton>
        ) : (
          <GlassButton
            onClick={handleToggleService}
            disabled={togglingService}
            className="!py-2 !px-5 text-[12px] border-cyan-500/30 hover:border-cyan-500/60"
          >
            {togglingService ? <i className="fa-solid fa-spinner fa-spin"></i> : 'Start Service'}
          </GlassButton>
        )}
      </div>
    </motion.div>
  );
}
