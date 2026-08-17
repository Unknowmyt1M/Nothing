'use client';
import { motion } from 'framer-motion';

export default function AnalyticsErrorState({ type = 'error', onRetry }) {
  const configs = {
    'not-authenticated': {
      icon: 'fa-solid fa-lock',
      title: 'Login to View Analytics',
      description: 'Connect your Google account to access YouTube channel analytics and insights.',
      action: { label: 'Go to Login', href: '/accounts' },
      accentColor: 'var(--color-cyan)',
    },
    'no-channel': {
      icon: 'fa-solid fa-link',
      title: 'Connect Your YouTube Channel',
      description: 'No YouTube channel is linked to your account. Link one to start viewing analytics.',
      action: { label: 'Go to Integrations', href: '/accounts' },
      accentColor: 'var(--color-purple)',
    },
    error: {
      icon: 'fa-solid fa-triangle-exclamation',
      title: 'Something Went Wrong',
      description: 'Failed to load analytics data. Please check your connection and try again.',
      action: { label: 'Retry', onClick: onRetry },
      accentColor: 'var(--color-pink)',
    },
    partial: {
      icon: 'fa-solid fa-circle-exclamation',
      title: 'Partial Data Unavailable',
      description: 'Some analytics data could not be loaded. Displaying available information.',
      action: null,
      accentColor: '#f1c40f',
    },
  };

  const config = configs[type] || configs.error;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel"
      style={{
        padding: '60px 40px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        gap: '20px',
      }}
    >
      <div
        style={{
          width: '80px',
          height: '80px',
          borderRadius: '50%',
          background: `${config.accentColor}15`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <i
          className={config.icon}
          style={{ fontSize: '36px', color: config.accentColor }}
        />
      </div>
      <h3
        style={{
          fontSize: '22px',
          fontWeight: '700',
          color: 'var(--color-text-primary)',
        }}
      >
        {config.title}
      </h3>
      <p
        style={{
          fontSize: '15px',
          color: 'var(--color-text-secondary)',
          maxWidth: '420px',
          lineHeight: '1.6',
        }}
      >
        {config.description}
      </p>
      {config.action && (
        config.action.href ? (
          <a
            href={config.action.href}
            className="btn-cyber"
            style={{
              padding: '12px 32px',
              fontSize: '14px',
              textDecoration: 'none',
              marginTop: '8px',
              display: 'inline-block',
            }}
          >
            {config.action.label}
          </a>
        ) : (
          <button
            className="btn-cyber"
            onClick={config.action.onClick}
            style={{
              padding: '12px 32px',
              fontSize: '14px',
              marginTop: '8px',
            }}
          >
            {config.action.label}
          </button>
        )
      )}
    </motion.div>
  );
}
