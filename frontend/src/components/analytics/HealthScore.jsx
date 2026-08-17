'use client';
import { useMemo } from 'react';
import { motion } from 'framer-motion';

function getGrade(score) {
  if (score >= 90) return { label: 'Excellent', color: '#2ecc71' };
  if (score >= 75) return { label: 'Good', color: 'var(--color-cyan)' };
  if (score >= 50) return { label: 'Fair', color: '#f1c40f' };
  if (score >= 25) return { label: 'Needs Work', color: 'var(--color-pink)' };
  return { label: 'Critical', color: 'var(--color-pink)' };
}

export default function HealthScore({ overview, channelData, videos, traffic }) {
  const scoreData = useMemo(() => {
    let score = 0;
    const factors = [];

    // Views trend (25%)
    const viewsTrend = overview?.trend?.views || channelData?.data?.viewsTrend || 0;
    const viewsScore = Math.min(25, Math.max(0, 25 * (1 + viewsTrend / 100)));
    score += viewsScore;
    factors.push({ label: 'Views Trend', value: viewsTrend, weight: 25, score: viewsScore });

    // Subscriber growth (25%)
    const subsGrowth = overview?.trend?.subscribers || channelData?.data?.subscriberGrowth || 0;
    const subsScore = Math.min(25, Math.max(0, 25 * (1 + subsGrowth / 100)));
    score += subsScore;
    factors.push({ label: 'Subscriber Growth', value: subsGrowth, weight: 25, score: subsScore });

    // Watch time trend (20%)
    const watchTrend = overview?.trend?.watchTime || channelData?.data?.watchTimeTrend || 0;
    const watchScore = Math.min(20, Math.max(0, 20 * (1 + watchTrend / 100)));
    score += watchScore;
    factors.push({ label: 'Watch Time Trend', value: watchTrend, weight: 20, score: watchScore });

    // Engagement rate (15%)
    const totalViews = overview?.views || overview?.totalViews || channelData?.data?.totalViews || 1;
    const totalLikes = overview?.likes || channelData?.data?.totalLikes || 0;
    const engagementRate = totalViews > 0 ? (totalLikes / totalViews) * 100 : 0;
    const engagementScore = Math.min(15, engagementRate * 15 * 20);
    score += engagementScore;
    factors.push({ label: 'Engagement Rate', value: engagementRate, weight: 15, score: engagementScore, isRate: true });

    // Upload consistency (15%)
    const videoCount = videos?.length || 0;
    const consistencyScore = Math.min(15, videoCount * 1.5);
    score += consistencyScore;
    factors.push({ label: 'Upload Consistency', value: videoCount, weight: 15, score: consistencyScore, isCount: true });

    const finalScore = Math.round(Math.min(100, Math.max(0, score)));
    const grade = getGrade(finalScore);

    return { score: finalScore, grade, factors };
  }, [overview, channelData, videos, traffic]);

  const { score, grade, factors } = scoreData;
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel"
      style={{ padding: '28px 32px' }}
    >
      <div
        style={{
          fontSize: '12px',
          color: 'var(--color-text-muted)',
          marginBottom: '16px',
          lineHeight: '1.4',
        }}
      >
        Nothing Channel Health Score — application-generated analytical score
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '40px',
          flexWrap: 'wrap',
        }}
      >
        {/* SVG Ring */}
        <div style={{ position: 'relative', width: '120px', height: '120px', flexShrink: 0 }}>
          <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="8"
            />
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke={grade.color}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              style={{
                transition: 'stroke-dashoffset 1s ease-out',
                filter: `drop-shadow(0 0 6px ${grade.color}60)`,
              }}
            />
          </svg>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '28px',
                fontWeight: '700',
                color: grade.color,
              }}
            >
              {score}
            </span>
            <span
              style={{
                fontSize: '10px',
                fontWeight: '600',
                color: grade.color,
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}
            >
              {grade.label}
            </span>
          </div>
        </div>

        {/* Breakdown */}
        <div style={{ flex: 1, minWidth: '220px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {factors.map((f, i) => {
              const pct = (f.score / f.weight) * 100;
              return (
                <div key={i}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginBottom: '4px',
                    }}
                  >
                    <span
                      style={{
                        fontSize: '13px',
                        color: 'var(--color-text-secondary)',
                      }}
                    >
                      {f.label}
                    </span>
                    <span
                      style={{
                        fontSize: '12px',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--color-text-muted)',
                      }}
                    >
                      {f.isRate
                        ? `${f.value.toFixed(2)}%`
                        : f.isCount
                        ? f.value
                        : `${f.value >= 0 ? '+' : ''}${f.value.toFixed(1)}%`}
                    </span>
                  </div>
                  <div
                    style={{
                      height: '4px',
                      background: 'rgba(255,255,255,0.06)',
                      borderRadius: '4px',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        width: `${pct}%`,
                        height: '100%',
                        background: grade.color,
                        borderRadius: '4px',
                        transition: 'width 1s ease-out',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
