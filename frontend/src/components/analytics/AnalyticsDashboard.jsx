'use client';
import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import AnalyticsErrorState from './AnalyticsErrorState';
import ChannelOverview from './ChannelOverview';
import DateRangeSelector from './DateRangeSelector';
import KpiCard from './KpiCard';
import ChartCard from './ChartCard';
import LineChart from './LineChart';
import TopVideosTable from './TopVideosTable';
import TrafficSources from './TrafficSources';
import InsightsPanel from './InsightsPanel';
import HealthScore from './HealthScore';
import ExportMenu from './ExportMenu';

function getDateRange(preset) {
  const now = new Date();
  const start = new Date();
  const end = new Date(now);
  start.setDate(now.getDate() - 28);
  return {
    start: start.toISOString().split('T')[0],
    end: end.toISOString().split('T')[0],
    label: 'Last 28 Days',
  };
}

function makeEndpoint(path, params) {
  const qs = new URLSearchParams(params).toString();
  return `/api/analytics/${path}?${qs}`;
}

function createDataState(data = null, loading = false, error = null) {
  return { data, loading, error };
}

export default function AnalyticsDashboard() {
  const [authStatus, setAuthStatus] = useState({ authenticated: false, user: null, youtube_channel: null });
  const [authLoading, setAuthLoading] = useState(true);
  const [channelId, setChannelId] = useState(null);
  const [channelName, setChannelName] = useState('');

  const defaultRange = getDateRange();
  const [startDate, setStartDate] = useState(defaultRange.start);
  const [endDate, setEndDate] = useState(defaultRange.end);
  const [dateLabel, setDateLabel] = useState(defaultRange.label);

  const [overview, setOverview] = useState(createDataState(null, true));
  const [channelData, setChannelData] = useState(createDataState(null, true));
  const [videos, setVideos] = useState(createDataState(null, true));
  const [traffic, setTraffic] = useState(createDataState(null, true));
  const [audience, setAudience] = useState(createDataState(null, true));
  const [revenue, setRevenue] = useState(createDataState(null, true));
  const [activeTab, setActiveTab] = useState('overview');

  const fetchAnalytics = useCallback(async (id, start, end) => {
    const params = { channel_id: id, start_date: start, end_date: end };

    setOverview(createDataState(null, true));
    setChannelData(createDataState(null, true));
    setVideos(createDataState(null, true));
    setTraffic(createDataState(null, true));
    setAudience(createDataState(null, true));
    setRevenue(createDataState(null, true));

    const endpoints = [
      { key: 'overview', path: 'overview' },
      { key: 'channelData', path: 'channel', params: { ...params } },
      { key: 'videos', path: 'videos', params: { ...params, limit: 10 } },
      { key: 'traffic', path: 'traffic', params: { ...params } },
      { key: 'audience', path: 'audience', params: { ...params } },
      { key: 'revenue', path: 'revenue', params: { ...params } },
    ];

    const setters = {
      overview: setOverview,
      channelData: setChannelData,
      videos: setVideos,
      traffic: setTraffic,
      audience: setAudience,
      revenue: setRevenue,
    };

    const fetches = endpoints.map(async ({ key, path, params: ep }) => {
      try {
        const url = ep
          ? makeEndpoint(path, ep)
          : `/api/analytics/${path}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setters[key](createDataState(data, false));
      } catch (err) {
        setters[key](createDataState(null, false, err.message));
      }
    });

    await Promise.allSettled(fetches);
  }, []);

  // Mount: fetch auth status
  useEffect(() => {
    const controller = new AbortController();
    (async () => {
      try {
        const res = await fetch('/api/auth/status', { signal: controller.signal });
        const data = await res.json();
        setAuthStatus(data);
        const id = data.youtube_channel?.id;
        if (data.authenticated && id) {
          setChannelId(id);
          setChannelName(data.youtube_channel.name || data.youtube_channel.title || '');
          fetchAnalytics(id, defaultRange.start, defaultRange.end);
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('Auth status fetch error:', err);
        }
      } finally {
        setAuthLoading(false);
      }
    })();
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleDateRangeChange = (start, end, label) => {
    setStartDate(start);
    setEndDate(end);
    setDateLabel(label);
    if (channelId) {
      fetchAnalytics(channelId, start, end);
    }
  };

  const handleRetry = () => {
    if (channelId) {
      fetchAnalytics(channelId, startDate, endDate);
    }
  };

  const anyLoading = overview.loading || channelData.loading || videos.loading;

  // Auth error states
  if (!authLoading && !authStatus.authenticated) {
    return (
      <div className="animate-fade-in" style={{ maxWidth: '900px', margin: '0 auto', width: '100%' }}>
        <AnalyticsErrorState type="not-authenticated" />
      </div>
    );
  }

  if (!authLoading && authStatus.authenticated && !channelId) {
    return (
      <div className="animate-fade-in" style={{ maxWidth: '900px', margin: '0 auto', width: '100%' }}>
        <AnalyticsErrorState type="no-channel" />
      </div>
    );
  }

  // Check for total failure
  const allFailed = !anyLoading &&
    overview.error && channelData.error && videos.error;

  if (allFailed) {
    return (
      <div className="animate-fade-in" style={{ maxWidth: '900px', margin: '0 auto', width: '100%' }}>
        <motion.h2
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          style={{
            fontSize: '32px',
            fontWeight: '800',
            background: 'linear-gradient(to right, var(--color-cyan), var(--color-pink))',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '35px',
          }}
        >
          CHANNEL ANALYTICS
        </motion.h2>
        <AnalyticsErrorState type="error" onRetry={handleRetry} />
      </div>
    );
  }

  // Check for partial failure
  const someFailed = !anyLoading &&
    (overview.error || channelData.error || videos.error);

  const kpiData = channelData?.data || {};
  const overviewData = overview?.data || {};
  const videosData = videos?.data || [];
  const videosArray = Array.isArray(videosData) ? videosData : videosData.videos || [];

  return (
    <div className="animate-fade-in" style={{ maxWidth: '1100px', margin: '0 auto', width: '100%' }}>
      {/* Page Title + Export */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '35px',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <motion.h2
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            style={{
              fontSize: '32px',
              fontWeight: '800',
              background: 'linear-gradient(to right, var(--color-cyan), var(--color-pink))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              marginBottom: '8px',
            }}
          >
            CHANNEL ANALYTICS
          </motion.h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '15px' }}>
            {channelName ? `Analytics for ${channelName}` : 'Channel performance overview'}
          </p>
        </div>
        <ExportMenu channelId={channelId} startDate={startDate} endDate={endDate} />
      </div>

      {/* Partial failure warning */}
      {someFailed && <AnalyticsErrorState type="partial" />}

      {/* Date Range */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: '24px' }}
      >
        <DateRangeSelector onChange={handleDateRangeChange} />
      </motion.div>

      {/* Channel Overview */}
      {overviewData.name && (
        <div style={{ marginBottom: '24px' }}>
          <ChannelOverview overview={overviewData} />
        </div>
      )}

      {/* Loading Skeletons for channel overview */}
      {!overviewData.name && overview.loading && (
        <div style={{ marginBottom: '24px' }}>
          <div
            className="glass-panel"
            style={{
              padding: '28px 32px',
              display: 'flex',
              alignItems: 'center',
              gap: '24px',
            }}
          >
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: 'rgba(255,255,255,0.05)',
                animation: 'pulse 1.5s infinite',
              }}
            />
            <div style={{ flex: 1 }}>
              <div
                style={{
                  height: '22px',
                  width: '200px',
                  background: 'rgba(255,255,255,0.05)',
                  borderRadius: '6px',
                  marginBottom: '8px',
                  animation: 'pulse 1.5s infinite',
                }}
              />
              <div
                style={{
                  height: '14px',
                  width: '120px',
                  background: 'rgba(255,255,255,0.03)',
                  borderRadius: '4px',
                  animation: 'pulse 1.5s infinite',
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '16px',
          marginBottom: '28px',
        }}
      >
        {anyLoading
          ? [1, 2, 3, 4, 5, 6].map((n) => (
              <div
                key={n}
                className="glass-panel"
                style={{
                  padding: '24px',
                  borderLeft: '4px solid rgba(255,255,255,0.05)',
                }}
              >
                <div
                  style={{
                    height: '14px',
                    width: '60%',
                    background: 'rgba(255,255,255,0.05)',
                    borderRadius: '4px',
                    marginBottom: '16px',
                    animation: 'pulse 1.5s infinite',
                  }}
                />
                <div
                  style={{
                    height: '28px',
                    width: '40%',
                    background: 'rgba(255,255,255,0.05)',
                    borderRadius: '6px',
                    animation: 'pulse 1.5s infinite',
                  }}
                />
              </div>
            ))
          : (
            <>
              <KpiCard
                icon="fa-solid fa-eye"
                value={kpiData.views ?? overviewData.views ?? 0}
                label="Views"
                trend={kpiData.viewsTrend ?? overviewData.trend?.views}
                accentColor="var(--color-cyan)"
              />
              <KpiCard
                icon="fa-solid fa-clock"
                value={kpiData.watchTimeMinutes ?? overviewData.watchTimeMinutes ?? 0}
                label="Watch Time"
                trend={kpiData.watchTimeTrend ?? overviewData.trend?.watchTime}
                accentColor="var(--color-purple)"
              />
              <KpiCard
                icon="fa-solid fa-users"
                value={kpiData.subscribers ?? overviewData.subscribers ?? 0}
                label="Subscribers"
                trend={kpiData.subscriberGrowth ?? overviewData.trend?.subscribers}
                accentColor="var(--color-pink)"
              />
              <KpiCard
                icon="fa-solid fa-thumbs-up"
                value={kpiData.likes ?? overviewData.likes ?? 0}
                label="Likes"
                trend={kpiData.likesTrend ?? overviewData.trend?.likes}
                accentColor="#2ecc71"
              />
              <KpiCard
                icon="fa-solid fa-comment"
                value={kpiData.comments ?? overviewData.comments ?? 0}
                label="Comments"
                trend={kpiData.commentsTrend ?? overviewData.trend?.comments}
                accentColor="#f1c40f"
              />
              <KpiCard
                icon="fa-solid fa-share-nodes"
                value={kpiData.shares ?? overviewData.shares ?? 0}
                label="Shares"
                trend={kpiData.sharesTrend ?? overviewData.trend?.shares}
                accentColor="var(--color-cyan)"
              />
            </>
          )}
      </div>

      {/* Views Chart */}
      <div style={{ marginBottom: '28px' }}>
        <ChartCard
          title="Views Over Time"
          subtitle={dateLabel}
        >
          {anyLoading ? (
            <div
              style={{
                height: '260px',
                background: 'rgba(255,255,255,0.02)',
                borderRadius: '8px',
                animation: 'pulse 1.5s infinite',
              }}
            />
          ) : (
            <LineChart
              data={
                (kpiData.viewsOverTime || overviewData.viewsOverTime || []).map(
                  (d) => ({ date: d.date || d.period, value: d.value || d.views || 0 })
                )
              }
              color="var(--color-cyan)"
              height={260}
              showDots={true}
              formatValue={(v) => new Intl.NumberFormat('en-US').format(v)}
            />
          )}
        </ChartCard>
      </div>

      {/* Tab Navigation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          display: 'flex',
          gap: '4px',
          marginBottom: '24px',
          padding: '4px',
          background: 'var(--bg-card)',
          borderRadius: '12px',
          border: '1px solid var(--color-border)',
          overflowX: 'auto',
          scrollbarWidth: 'none',
        }}
      >
        {[
          { id: 'overview', label: 'Overview', icon: 'fa-solid fa-chart-line' },
          { id: 'videos', label: 'Videos', icon: 'fa-solid fa-video' },
          { id: 'traffic', label: 'Traffic', icon: 'fa-solid fa-diagram-project' },
          { id: 'audience', label: 'Audience', icon: 'fa-solid fa-users' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              flex: '1 1 0',
              padding: '12px 20px',
              borderRadius: '10px',
              border: 'none',
              background: activeTab === tab.id ? 'rgba(0, 242, 254, 0.12)' : 'transparent',
              color: activeTab === tab.id ? 'var(--color-cyan)' : 'var(--color-text-muted)',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'all 0.2s ease',
              whiteSpace: 'nowrap',
            }}
          >
            <i className={tab.icon} style={{ fontSize: '13px' }} />
            {tab.label}
          </button>
        ))}
      </motion.div>

      {/* Tab Content */}
      <div style={{ marginBottom: '28px' }}>
        {activeTab === 'overview' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}
          >
            <ChartCard title="Watch Time Trend" subtitle="Minutes watched over time">
              {anyLoading ? (
                <div
                  style={{
                    height: '260px',
                    background: 'rgba(255,255,255,0.02)',
                    borderRadius: '8px',
                    animation: 'pulse 1.5s infinite',
                  }}
                />
              ) : (
                <LineChart
                  data={
                    (kpiData.watchTimeOverTime || overviewData.watchTimeOverTime || []).map(
                      (d) => ({ date: d.date || d.period, value: d.value || d.watchTime || 0 })
                    )
                  }
                  color="var(--color-purple)"
                  height={240}
                  showDots={true}
                  formatValue={(v) => `${Math.round(v)}m`}
                />
              )}
            </ChartCard>
          </motion.div>
        )}

        {activeTab === 'videos' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <ChartCard title="Top Performing Videos" subtitle={`Period: ${dateLabel}`}>
              {anyLoading ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <div
                      key={n}
                      style={{
                        height: '64px',
                        borderRadius: '8px',
                        background: 'rgba(255,255,255,0.03)',
                        animation: 'pulse 1.5s infinite',
                      }}
                    />
                  ))}
                </div>
              ) : (
                <TopVideosTable videos={videosArray} />
              )}
            </ChartCard>
          </motion.div>
        )}

        {activeTab === 'traffic' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <TrafficSources traffic={traffic} audience={audience} />
          </motion.div>
        )}

        {activeTab === 'audience' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}
          >
            {/* Gender / Age breakdown */}
            <ChartCard title="Audience Demographics" subtitle="Viewer demographics breakdown">
              {anyLoading ? (
                <div
                  style={{
                    height: '180px',
                    background: 'rgba(255,255,255,0.02)',
                    borderRadius: '8px',
                    animation: 'pulse 1.5s infinite',
                  }}
                />
              ) : (
                <AudienceDemographics audience={audience?.data} />
              )}
            </ChartCard>
          </motion.div>
        )}
      </div>

      {/* Insights + Health Score */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: '24px',
          marginBottom: '40px',
        }}
      >
        <InsightsPanel
          channelData={channelData}
          videos={videosArray}
          traffic={traffic}
          overview={overviewData}
        />
        <HealthScore
          overview={overviewData}
          channelData={channelData}
          videos={videosArray}
          traffic={traffic}
        />
      </div>
    </div>
  );
}

function AudienceDemographics({ audience }) {
  const countries = audience?.countries || [];
  const devices = audience?.devices || [];
  const ageRanges = audience?.ageRanges || audience?.age_ranges || [];
  const genderSplit = audience?.genderSplit || audience?.gender_split || null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Age Ranges */}
      {ageRanges.length > 0 && (
        <div>
          <h4
            style={{
              fontSize: '13px',
              fontWeight: '700',
              color: 'var(--color-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: '12px',
            }}
          >
            Age Distribution
          </h4>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {ageRanges.map((ar, i) => (
              <div
                key={i}
                className="glass-panel"
                style={{
                  padding: '14px 18px',
                  flex: '1 1 100px',
                  textAlign: 'center',
                }}
              >
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '18px',
                    fontWeight: '700',
                    color: 'var(--color-cyan)',
                  }}
                >
                  {ar.percentage || ar.value || 0}%
                </div>
                <div
                  style={{
                    fontSize: '12px',
                    color: 'var(--color-text-muted)',
                    marginTop: '4px',
                  }}
                >
                  {ar.range || ar.age || 'Unknown'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Gender Split */}
      {genderSplit && (
        <div>
          <h4
            style={{
              fontSize: '13px',
              fontWeight: '700',
              color: 'var(--color-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: '12px',
            }}
          >
            Gender
          </h4>
          <div style={{ display: 'flex', gap: '12px' }}>
            {Object.entries(genderSplit).map(([gender, pct]) => (
              <div
                key={gender}
                className="glass-panel"
                style={{
                  padding: '16px 24px',
                  flex: 1,
                  textAlign: 'center',
                }}
              >
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '22px',
                    fontWeight: '700',
                    color: gender === 'male' ? 'var(--color-cyan)' : gender === 'female' ? 'var(--color-pink)' : 'var(--color-purple)',
                  }}
                >
                  {pct}%
                </div>
                <div
                  style={{
                    fontSize: '12px',
                    color: 'var(--color-text-muted)',
                    marginTop: '4px',
                    textTransform: 'capitalize',
                  }}
                >
                  {gender}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Countries */}
      {countries.length > 0 && (
        <div>
          <h4
            style={{
              fontSize: '13px',
              fontWeight: '700',
              color: 'var(--color-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: '12px',
            }}
          >
            Top Countries
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {countries.slice(0, 8).map((c, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '8px 0',
                }}
              >
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    color: 'var(--color-text-muted)',
                    minWidth: '24px',
                  }}
                >
                  {i + 1}.
                </span>
                <span style={{ flex: 1, fontSize: '14px', color: 'var(--color-text-secondary)' }}>
                  {c.country || c.name || 'Unknown'}
                </span>
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                    fontWeight: '600',
                    color: 'var(--color-text-primary)',
                  }}
                >
                  {new Intl.NumberFormat('en-US').format(c.views || c.value || c.count || 0)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Devices */}
      {devices.length > 0 && (
        <div>
          <h4
            style={{
              fontSize: '13px',
              fontWeight: '700',
              color: 'var(--color-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: '12px',
            }}
          >
            Devices
          </h4>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {devices.map((d, i) => (
              <div
                key={i}
                className="glass-panel"
                style={{ padding: '16px 20px', flex: '1 1 120px', textAlign: 'center' }}
              >
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '20px',
                    fontWeight: '700',
                    color: 'var(--color-cyan)',
                  }}
                >
                  {d.percentage || 0}%
                </div>
                <div
                  style={{
                    fontSize: '12px',
                    color: 'var(--color-text-muted)',
                    marginTop: '4px',
                    textTransform: 'capitalize',
                  }}
                >
                  {d.device || d.type || 'Unknown'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
