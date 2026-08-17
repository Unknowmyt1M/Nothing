'use client';
import { useMemo } from 'react';
import { motion } from 'framer-motion';

export default function InsightsPanel({ channelData, videos, traffic, overview }) {
  const insights = useMemo(() => {
    const result = [];
    const data = channelData?.data || {};
    const videoList = videos || [];
    const overviewData = overview || {};

    // View trend
    const viewsTrend = data.viewsTrend || overviewData.trend?.views || null;
    if (viewsTrend != null) {
      result.push({
        icon: viewsTrend >= 0 ? 'fa-solid fa-arrow-trend-up' : 'fa-solid fa-arrow-trend-down',
        color: viewsTrend >= 0 ? '#2ecc71' : 'var(--color-pink)',
        text: `Views are ${viewsTrend >= 0 ? 'up' : 'down'} ${Math.abs(viewsTrend).toFixed(1)}% compared to the previous period.`,
      });
    }

    // Top video contribution
    if (videoList.length > 0 && overviewData.views) {
      const topViews = videoList[0]?.views || 0;
      const totalViews = overviewData.views;
      if (totalViews > 0) {
        const contribution = ((topViews / totalViews) * 100).toFixed(1);
        result.push({
          icon: 'fa-solid fa-play-circle',
          color: 'var(--color-cyan)',
          text: `Your top video accounts for ${contribution}% of total views in this period.`,
        });
      }
    }

    // Strongest traffic source
    const sources = traffic?.data?.sources || traffic?.data?.traffic_sources || [];
    if (sources.length > 0) {
      const top = sources.reduce((max, s) =>
        (s.visits || s.value || s.count || 0) > (max.visits || max.value || max.count || 0) ? s : max
      , sources[0]);
      result.push({
        icon: 'fa-solid fa-diagram-project',
        color: 'var(--color-purple)',
        text: `Strongest traffic source: ${top.source || top.name || 'Unknown'}.`,
      });
    }

    // Subscriber growth
    const subsGrowth = data.subscriberGrowth || overviewData.trend?.subscribers || null;
    if (subsGrowth != null) {
      result.push({
        icon: 'fa-solid fa-users',
        color: subsGrowth >= 0 ? '#2ecc71' : 'var(--color-pink)',
        text: `Subscriber count ${subsGrowth >= 0 ? 'grew' : 'declined'} by ${Math.abs(subsGrowth).toFixed(1)}%.`,
      });
    }

    // Watch time
    const watchTrend = data.watchTimeTrend || overviewData.trend?.watchTime || null;
    if (watchTrend != null) {
      result.push({
        icon: 'fa-solid fa-clock',
        color: watchTrend >= 0 ? '#2ecc71' : 'var(--color-pink)',
        text: `Watch time ${watchTrend >= 0 ? 'increased' : 'decreased'} by ${Math.abs(watchTrend).toFixed(1)}%.`,
      });
    }

    return result;
  }, [channelData, videos, traffic, overview]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel"
      style={{ padding: '28px 32px' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
        <i className="fa-solid fa-lightbulb" style={{ color: '#f1c40f', fontSize: '18px' }} />
        <h3 style={{ fontSize: '17px', fontWeight: '700', color: 'var(--color-text-primary)' }}>
          Nothing Insights
        </h3>
      </div>
      <p
        style={{
          fontSize: '12px',
          color: 'var(--color-text-muted)',
          marginBottom: '20px',
          lineHeight: '1.4',
        }}
      >
        Application-generated analysis, not official YouTube metrics
      </p>

      {insights.length === 0 ? (
        <p
          style={{
            fontSize: '14px',
            color: 'var(--color-text-muted)',
            padding: '20px 0',
            textAlign: 'center',
          }}
        >
          Not enough data to generate insights yet.
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {insights.map((insight, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                padding: '12px 16px',
                background: 'rgba(255,255,255,0.02)',
                borderRadius: '10px',
                border: '1px solid var(--color-border)',
              }}
            >
              <i
                className={insight.icon}
                style={{
                  fontSize: '14px',
                  color: insight.color,
                  marginTop: '2px',
                  flexShrink: 0,
                }}
              />
              <span
                style={{
                  fontSize: '14px',
                  color: 'var(--color-text-secondary)',
                  lineHeight: '1.5',
                }}
              >
                {insight.text}
              </span>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
