'use client';
import { motion } from 'framer-motion';

export default function ChartCard({ title, subtitle, children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel"
      style={{ padding: '24px' }}
    >
      {title && (
        <div style={{ marginBottom: subtitle ? '4px' : '20px' }}>
          <h3
            style={{
              fontSize: '16px',
              fontWeight: '700',
              color: 'var(--color-text-primary)',
            }}
          >
            {title}
          </h3>
          {subtitle && (
            <p
              style={{
                fontSize: '13px',
                color: 'var(--color-text-muted)',
                marginTop: '2px',
              }}
            >
              {subtitle}
            </p>
          )}
        </div>
      )}
      {children}
    </motion.div>
  );
}
