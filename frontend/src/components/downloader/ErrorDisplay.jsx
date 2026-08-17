'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const ERROR_ICONS = {
  INVALID_URL: 'fa-link',
  UNSUPPORTED_PLATFORM: 'fa-globe',
  UNSUPPORTED_URL_TYPE: 'fa-ban',
  CONTENT_UNAVAILABLE: 'fa-film',
  PRIVATE_CONTENT: 'fa-lock',
  AUTHENTICATION_REQUIRED: 'fa-right-to-bracket',
  REGION_RESTRICTED: 'fa-earth-americas',
  FORMAT_UNAVAILABLE: 'fa-sliders',
  NETWORK_ERROR: 'fa-wifi',
  TIMEOUT: 'fa-hourglass-half',
  RATE_LIMITED: 'fa-gauge-high',
  EXTRACTION_ERROR: 'fa-magnifying-glass',
  DOWNLOAD_ERROR: 'fa-download',
  MERGE_ERROR: 'fa-code-merge',
  FFMPEG_ERROR: 'fa-film',
  STORAGE_ERROR: 'fa-hard-drive',
  FILE_TOO_LARGE: 'fa-weight-scale',
  DOWNLOAD_CANCELLED: 'fa-ban',
  BOT_CHECK: 'fa-robot',
  AGE_RESTRICTED: 'fa-user-shield',
  YOUTUBE_AUTH_EXPIRED: 'fa-right-to-bracket',
  DATABASE_ERROR: 'fa-database',
  NOT_FOUND: 'fa-circle-question',
  UNKNOWN_ERROR: 'fa-triangle-exclamation',
};

const ERROR_COLORS = {
  INVALID_URL: { border: '#f59e0b', glow: 'rgba(245, 158, 11, 0.15)' },
  UNSUPPORTED_PLATFORM: { border: '#8b5cf6', glow: 'rgba(139, 92, 246, 0.15)' },
  UNSUPPORTED_URL_TYPE: { border: '#f97316', glow: 'rgba(249, 115, 22, 0.15)' },
  CONTENT_UNAVAILABLE: { border: '#ef4444', glow: 'rgba(239, 68, 68, 0.15)' },
  PRIVATE_CONTENT: { border: '#f59e0b', glow: 'rgba(245, 158, 11, 0.15)' },
  AUTHENTICATION_REQUIRED: { border: '#3b82f6', glow: 'rgba(59, 130, 246, 0.15)' },
  REGION_RESTRICTED: { border: '#8b5cf6', glow: 'rgba(139, 92, 246, 0.15)' },
  FORMAT_UNAVAILABLE: { border: '#06b6d4', glow: 'rgba(6, 182, 212, 0.15)' },
  NETWORK_ERROR: { border: '#f97316', glow: 'rgba(249, 115, 22, 0.15)' },
  TIMEOUT: { border: '#f97316', glow: 'rgba(249, 115, 22, 0.15)' },
  RATE_LIMITED: { border: '#f59e0b', glow: 'rgba(245, 158, 11, 0.15)' },
  EXTRACTION_ERROR: { border: '#ef4444', glow: 'rgba(239, 68, 68, 0.15)' },
  DOWNLOAD_ERROR: { border: '#ef4444', glow: 'rgba(239, 68, 68, 0.15)' },
  MERGE_ERROR: { border: '#ef4444', glow: 'rgba(239, 68, 68, 0.15)' },
  FFMPEG_ERROR: { border: '#ef4444', glow: 'rgba(239, 68, 68, 0.15)' },
  STORAGE_ERROR: { border: '#ef4444', glow: 'rgba(239, 68, 68, 0.15)' },
  FILE_TOO_LARGE: { border: '#f59e0b', glow: 'rgba(245, 158, 11, 0.15)' },
  DOWNLOAD_CANCELLED: { border: '#06b6d4', glow: 'rgba(6, 182, 212, 0.15)' },
  BOT_CHECK: { border: '#ef4444', glow: 'rgba(239, 68, 68, 0.15)' },
  AGE_RESTRICTED: { border: '#8b5cf6', glow: 'rgba(139, 92, 246, 0.15)' },
  YOUTUBE_AUTH_EXPIRED: { border: '#3b82f6', glow: 'rgba(59, 130, 246, 0.15)' },
  DATABASE_ERROR: { border: '#ef4444', glow: 'rgba(239, 68, 68, 0.15)' },
  NOT_FOUND: { border: '#6b7280', glow: 'rgba(107, 114, 128, 0.15)' },
  UNKNOWN_ERROR: { border: '#ef4444', glow: 'rgba(239, 68, 68, 0.15)' },
};

export default function ErrorDisplay({ error, onRetry, onDismiss, className = '' }) {
  const [showDetails, setShowDetails] = useState(false);

  if (!error) return null;

  const code = error.code || 'UNKNOWN_ERROR';
  const icon = ERROR_ICONS[code] || 'fa-triangle-exclamation';
  const colors = ERROR_COLORS[code] || ERROR_COLORS.UNKNOWN_ERROR;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 10, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.98 }}
        className={className}
        style={{
          background: `linear-gradient(135deg, rgba(5, 4, 12, 0.95), rgba(15, 12, 30, 0.95))`,
          border: `1px solid ${colors.border}33`,
          borderLeft: `3px solid ${colors.border}`,
          borderRadius: '12px',
          padding: '20px 24px',
          boxShadow: `0 4px 20px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.03), 0 0 30px ${colors.glow}`,
          backdropFilter: 'blur(12px)',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
          {/* Icon */}
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: `${colors.border}18`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}>
            <i className={`fa-solid ${icon}`} style={{ color: colors.border, fontSize: '16px' }}></i>
          </div>

          {/* Content */}
          <div style={{ flex: 1, minWidth: 0 }}>
            {/* Title */}
            <div style={{
              fontSize: '14px',
              fontWeight: '700',
              color: '#ffffff',
              marginBottom: '6px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              {error.title || 'Something went wrong'}
              {error.retryable && (
                <span style={{
                  fontSize: '9px',
                  fontWeight: '600',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  color: colors.border,
                  background: `${colors.border}18`,
                  padding: '2px 7px',
                  borderRadius: '4px',
                }}>
                  Retryable
                </span>
              )}
            </div>

            {/* Message */}
            <p style={{
              fontSize: '13px',
              color: 'var(--color-text-secondary, #9ca3af)',
              lineHeight: '1.5',
              margin: '0 0 8px 0',
            }}>
              {error.message}
            </p>

            {/* Suggestion */}
            {error.suggestion && (
              <div style={{
                fontSize: '12px',
                color: 'var(--color-cyan, #00f2fe)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                marginBottom: '12px',
              }}>
                <i className="fa-solid fa-lightbulb" style={{ fontSize: '10px' }}></i>
                <span>{error.suggestion}</span>
              </div>
            )}

            {/* Actions */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '4px' }}>
              {error.retryable && onRetry && (
                <button
                  onClick={onRetry}
                  style={{
                    background: `${colors.border}20`,
                    border: `1px solid ${colors.border}40`,
                    color: colors.border,
                    padding: '7px 16px',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = `${colors.border}30`;
                    e.currentTarget.style.borderColor = `${colors.border}70`;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = `${colors.border}20`;
                    e.currentTarget.style.borderColor = `${colors.border}40`;
                  }}
                >
                  <i className="fa-solid fa-rotate-right" style={{ fontSize: '11px' }}></i>
                  Try Again
                </button>
              )}

              {error.details && (
                <button
                  onClick={() => setShowDetails(!showDetails)}
                  style={{
                    background: 'transparent',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    color: 'var(--color-text-muted, #6b7280)',
                    padding: '7px 12px',
                    borderRadius: '8px',
                    fontSize: '11px',
                    fontWeight: '500',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.15)';
                    e.currentTarget.style.color = 'var(--color-text-secondary, #9ca3af)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                    e.currentTarget.style.color = 'var(--color-text-muted, #6b7280)';
                  }}
                >
                  <i className={`fa-solid fa-chevron-${showDetails ? 'up' : 'down'}`} style={{ fontSize: '9px' }}></i>
                  Technical Details
                </button>
              )}

              {onDismiss && (
                <button
                  onClick={onDismiss}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--color-text-muted, #6b7280)',
                    padding: '7px 8px',
                    borderRadius: '8px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    marginLeft: 'auto',
                    transition: 'color 0.2s ease',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.color = '#ffffff'}
                  onMouseLeave={(e) => e.currentTarget.style.color = 'var(--color-text-muted, #6b7280)'}
                >
                  <i className="fa-solid fa-xmark"></i>
                </button>
              )}
            </div>

            {/* Expandable technical details */}
            <AnimatePresence>
              {showDetails && error.details && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  style={{ overflow: 'hidden' }}
                >
                  <pre style={{
                    marginTop: '12px',
                    padding: '12px 14px',
                    background: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.05)',
                    borderRadius: '8px',
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono, monospace)',
                    color: 'var(--color-text-muted, #6b7280)',
                    lineHeight: '1.6',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                    maxHeight: '120px',
                    overflowY: 'auto',
                  }}>
                    {error.details}
                  </pre>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
