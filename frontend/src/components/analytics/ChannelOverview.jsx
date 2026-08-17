'use client';
import { motion } from 'framer-motion';

function formatNumber(n) {
  if (n == null) return '—';
  return new Intl.NumberFormat('en-US').format(n);
}

export default function ChannelOverview({ overview }) {
  const name = overview?.name || overview?.channelName || 'Channel';
  const avatar = overview?.avatar || overview?.thumbnailUrl;
  const subscribers = overview?.subscribers || overview?.subscriberCount;
  const videoCount = overview?.videoCount || overview?.videos;
  const totalViews = overview?.totalViews || overview?.viewCount || overview?.views;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel"
      style={{
        padding: '28px 32px',
        display: 'flex',
        alignItems: 'center',
        gap: '24px',
        flexWrap: 'wrap',
      }}
    >
      {avatar && (
        <img
          src={avatar}
          alt={name}
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            border: '2px solid var(--color-cyan)',
            objectFit: 'cover',
          }}
        />
      )}
      {!avatar && (
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            background: 'rgba(0, 242, 254, 0.1)',
            border: '2px solid var(--color-cyan)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <i
            className="fa-solid fa-tv"
            style={{ fontSize: '24px', color: 'var(--color-cyan)' }}
          />
        </div>
      )}

      <div style={{ flex: 1, minWidth: '180px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <h3
            style={{
              fontSize: '22px',
              fontWeight: '700',
              color: 'var(--color-text-primary)',
            }}
          >
            {name}
          </h3>
          <span
            style={{
              padding: '4px 12px',
              borderRadius: '20px',
              fontSize: '11px',
              fontWeight: '700',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              background: 'rgba(46, 204, 113, 0.15)',
              color: '#2ecc71',
              border: '1px solid rgba(46, 204, 113, 0.3)',
            }}
          >
            <i className="fa-solid fa-circle-check" style={{ marginRight: '5px', fontSize: '9px' }} />
            Connected
          </span>
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          gap: '32px',
          flexWrap: 'wrap',
        }}
      >
        {[
          { label: 'Subscribers', value: subscribers },
          { label: 'Videos', value: videoCount },
          { label: 'Total Views', value: totalViews },
        ].map(({ label, value }) => (
          <div key={label} style={{ textAlign: 'center' }}>
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '20px',
                fontWeight: '700',
                color: 'var(--color-text-primary)',
              }}
            >
              {formatNumber(value)}
            </div>
            <div
              style={{
                fontSize: '12px',
                color: 'var(--color-text-muted)',
                marginTop: '2px',
              }}
            >
              {label}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
