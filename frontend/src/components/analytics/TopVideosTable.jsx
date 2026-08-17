'use client';
import { motion } from 'framer-motion';

function formatNumber(n) {
  if (n == null) return '—';
  return new Intl.NumberFormat('en-US').format(n);
}

function formatDuration(minutes) {
  if (minutes == null) return '—';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export default function TopVideosTable({ videos = [] }) {
  if (!videos.length) {
    return (
      <div
        style={{
          padding: '40px',
          textAlign: 'center',
          color: 'var(--color-text-muted)',
          fontSize: '14px',
        }}
      >
        No video data available
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {/* Desktop Table */}
      <div
        style={{
          overflowX: 'auto',
          scrollbarWidth: 'thin',
        }}
      >
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            minWidth: '700px',
          }}
        >
          <thead>
            <tr>
              {['#', 'Video', 'Views', 'Watch Time', 'Likes', 'Comments', 'Subs'].map(
                (h) => (
                  <th
                    key={h}
                    style={{
                      padding: '12px 16px',
                      textAlign: 'left',
                      fontSize: '11px',
                      fontWeight: '700',
                      color: 'var(--color-text-muted)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                      borderBottom: '1px solid var(--color-border)',
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    {h}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {videos.map((video, i) => (
              <tr
                key={video.id || i}
                style={{
                  transition: 'background 0.2s ease',
                  cursor: 'pointer',
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.background = 'rgba(0, 242, 254, 0.04)')
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.background = 'transparent')
                }
                onClick={() => {
                  if (video.url) window.open(video.url, '_blank');
                }}
              >
                <td
                  style={{
                    padding: '14px 16px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                    color: 'var(--color-text-muted)',
                    borderBottom: '1px solid var(--color-border)',
                  }}
                >
                  {i + 1}
                </td>
                <td
                  style={{
                    padding: '14px 16px',
                    borderBottom: '1px solid var(--color-border)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {video.thumbnail && (
                      <img
                        src={video.thumbnail}
                        alt=""
                        style={{
                          width: '80px',
                          height: '45px',
                          borderRadius: '6px',
                          objectFit: 'cover',
                          flexShrink: 0,
                        }}
                      />
                    )}
                    <span
                      style={{
                        fontSize: '14px',
                        color: 'var(--color-text-primary)',
                        fontWeight: '500',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        maxWidth: '260px',
                      }}
                    >
                      {video.title || 'Untitled'}
                    </span>
                  </div>
                </td>
                <td
                  style={{
                    padding: '14px 16px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                    fontWeight: '600',
                    color: 'var(--color-text-primary)',
                    borderBottom: '1px solid var(--color-border)',
                  }}
                >
                  {formatNumber(video.views)}
                </td>
                <td
                  style={{
                    padding: '14px 16px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                    fontWeight: '600',
                    color: 'var(--color-text-primary)',
                    borderBottom: '1px solid var(--color-border)',
                  }}
                >
                  {formatDuration(video.watchTimeMinutes || video.watch_time_minutes)}
                </td>
                <td
                  style={{
                    padding: '14px 16px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                    fontWeight: '600',
                    color: 'var(--color-text-primary)',
                    borderBottom: '1px solid var(--color-border)',
                  }}
                >
                  {formatNumber(video.likes)}
                </td>
                <td
                  style={{
                    padding: '14px 16px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                    fontWeight: '600',
                    color: 'var(--color-text-primary)',
                    borderBottom: '1px solid var(--color-border)',
                  }}
                >
                  {formatNumber(video.comments)}
                </td>
                <td
                  style={{
                    padding: '14px 16px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                    fontWeight: '600',
                    color: 'var(--color-cyan)',
                    borderBottom: '1px solid var(--color-border)',
                  }}
                >
                  {formatNumber(video.subsGained || video.subs_gained)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card Layout */}
      <div style={{ display: 'none' }}>
        <style>{`
          @media (max-width: 768px) {
            .analytics-table-desktop { display: none !important; }
            .analytics-table-mobile { display: flex !important; }
          }
        `}</style>
      </div>
      <div
        className="analytics-table-mobile"
        style={{
          display: 'none',
          flexDirection: 'column',
          gap: '12px',
          padding: '4px 0',
        }}
      >
        {videos.map((video, i) => (
          <div
            key={video.id || i}
            className="glass-panel"
            style={{
              padding: '16px',
              display: 'flex',
              gap: '14px',
              alignItems: 'center',
              cursor: 'pointer',
            }}
            onClick={() => {
              if (video.url) window.open(video.url, '_blank');
            }}
          >
            {video.thumbnail && (
              <img
                src={video.thumbnail}
                alt=""
                style={{
                  width: '90px',
                  height: '50px',
                  borderRadius: '6px',
                  objectFit: 'cover',
                  flexShrink: 0,
                }}
              />
            )}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontSize: '14px',
                  fontWeight: '600',
                  color: 'var(--color-text-primary)',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {i + 1}. {video.title || 'Untitled'}
              </div>
              <div
                style={{
                  display: 'flex',
                  gap: '16px',
                  marginTop: '8px',
                  flexWrap: 'wrap',
                }}
              >
                {[
                  { label: 'Views', val: formatNumber(video.views) },
                  { label: 'Likes', val: formatNumber(video.likes) },
                  { label: 'Comments', val: formatNumber(video.comments) },
                ].map(({ label, val }) => (
                  <span
                    key={label}
                    style={{
                      fontSize: '12px',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--color-text-muted)',
                    }}
                  >
                    {label}:{' '}
                    <span style={{ color: 'var(--color-text-primary)' }}>{val}</span>
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
