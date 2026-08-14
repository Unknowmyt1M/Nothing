import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import Toast from '@/components/Toast';
import ServiceControlCard from './ServiceControlCard';
import AddFeedForm from './AddFeedForm';
import MonitoredFeedsList from './MonitoredFeedsList';
import LiveScanStream from './LiveScanStream';

export default function AutomationHub() {
  const [channels, setChannels] = useState([]);
  const [loadingChannels, setLoadingChannels] = useState(true);
  
  // Add channel state
  const [channelUrl, setChannelUrl] = useState('');
  const [analyzingUrl, setAnalyzingUrl] = useState(false);
  const [analyzedChannel, setAnalyzedChannel] = useState(null);
  
  // Monitoring service state
  const [serviceActive, setServiceActive] = useState(false);
  const [togglingService, setTogglingService] = useState(false);
  
  // Console logs state
  const [logs, setLogs] = useState([]);
  const [clearingLogs, setClearingLogs] = useState(false);
  
  // Toast notifications
  const [toast, setToast] = useState({ message: '', type: 'info' });
  const terminalEndRef = useRef(null);

  const triggerToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast({ message: '', type: 'info' });
    }, 4500);
  };

  // Fetch monitored channels
  const fetchChannels = async () => {
    try {
      const res = await fetch('/api/automation/get_channels');
      const data = await res.json();
      if (!data.error) {
        setChannels(data.channels || []);
      }
    } catch (err) {
      console.error('Error fetching channels:', err);
    } finally {
      setLoadingChannels(false);
    }
  };

  // Poll logs and service status
  const pollLogsAndStatus = async () => {
    try {
      const res = await fetch('/api/automation/get_logs');
      const data = await res.json();
      if (!data.error) {
        setLogs(data.logs || []);
        setServiceActive(data.service_status);
      }
    } catch (err) {
      console.error('Error fetching logs:', err);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchChannels();
      pollLogsAndStatus();
    }, 0);

    // Set interval to poll logs and service status every 2 seconds
    const interval = setInterval(pollLogsAndStatus, 2000);
    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, []);

  // Auto-scroll terminal to bottom on new logs
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Handle Channel analysis
  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!channelUrl.trim()) return;

    setAnalyzingUrl(true);
    setAnalyzedChannel(null);
    try {
      const res = await fetch('/api/automation/fetch_channel_info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_url: channelUrl })
      });
      const data = await res.json();
      
      if (data.error) {
        throw new Error(data.error);
      }
      setAnalyzedChannel(data);
      triggerToast('Channel details successfully parsed!', 'success');
    } catch (err) {
      triggerToast(err.message, 'error');
    } finally {
      setAnalyzingUrl(false);
    }
  };

  // Add analyzed channel to database
  const handleAddChannel = async () => {
    if (!analyzedChannel) return;

    try {
      const res = await fetch('/api/automation/add_channel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_info: analyzedChannel })
      });
      const data = await res.json();

      if (data.error) {
        throw new Error(data.error);
      }
      
      triggerToast(`${analyzedChannel.name} registered for monitoring!`, 'success');
      setAnalyzedChannel(null);
      setChannelUrl('');
      fetchChannels();
    } catch (err) {
      triggerToast(err.message, 'error');
    }
  };

  // Remove channel from monitoring
  const handleRemoveChannel = async (channelId, name) => {
    if (!confirm(`Are you sure you want to stop monitoring ${name}?`)) return;

    try {
      const res = await fetch('/api/automation/remove_channel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_id: channelId })
      });
      const data = await res.json();

      if (data.error) {
        throw new Error(data.error);
      }

      triggerToast(`Removed channel: ${name}`, 'info');
      fetchChannels();
    } catch (err) {
      triggerToast(err.message, 'error');
    }
  };

  // Toggle monitoring service status
  const handleToggleService = async () => {
    setTogglingService(true);
    const endpoint = serviceActive ? 'stop_monitoring' : 'start_monitoring';
    const actionText = serviceActive ? 'Deactivating' : 'Activating';
    
    try {
      triggerToast(`${actionText} background scan pipeline...`, 'info');
      const res = await fetch(`/api/automation/${endpoint}`, { method: 'POST' });
      const data = await res.json();
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      setServiceActive(!serviceActive);
      triggerToast(`Pipeline status updated successfully!`, 'success');
      pollLogsAndStatus();
    } catch (err) {
      triggerToast(err.message, 'error');
    } finally {
      setTogglingService(false);
    }
  };

  // Clear log data
  const handleClearLogs = async () => {
    setClearingLogs(true);
    try {
      const res = await fetch('/api/automation/clear_logs', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setLogs([]);
        triggerToast('Hacker terminal log console cleared.', 'success');
      } else {
        throw new Error(data.error || 'Failed to clear logs');
      }
    } catch (err) {
      triggerToast(err.message, 'error');
    } finally {
      setClearingLogs(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ maxWidth: '1100px', margin: '0 auto', width: '100%' }}>
      {/* Page Title */}
      <div style={{ marginBottom: '35px' }}>
        <motion.h2 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          style={{ 
            fontSize: '32px', 
            fontWeight: '800', 
            background: 'linear-gradient(to right, #00f2fe, #ff007f)', 
            WebkitBackgroundClip: 'text', 
            WebkitTextFillColor: 'transparent', 
            marginBottom: '8px' 
          }}
        >
          AUTOMATED SCANNING HUB
        </motion.h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '15px' }}>
          Monitor YouTube feeds for new uploads, extract profiles, and auto-download/auto-publish them synchronously.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '30px', alignItems: 'start' }}>
        
        {/* Left Side: Service Switch, Channel additions, and Monitored Lists */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
          
          {/* Active Monitoring Service Control */}
          <ServiceControlCard 
            serviceActive={serviceActive}
            togglingService={togglingService}
            handleToggleService={handleToggleService}
          />

          {/* Add YouTube Channel Monitored form */}
          <AddFeedForm 
            channelUrl={channelUrl}
            setChannelUrl={setChannelUrl}
            analyzingUrl={analyzingUrl}
            analyzedChannel={analyzedChannel}
            handleAnalyze={handleAnalyze}
            handleAddChannel={handleAddChannel}
          />

          {/* Monitored Channels Grid list */}
          <MonitoredFeedsList 
            loadingChannels={loadingChannels}
            channels={channels}
            handleRemoveChannel={handleRemoveChannel}
          />
        </div>

        {/* Right Side: Hacker Scroll terminal */}
        <LiveScanStream 
          logs={logs}
          clearingLogs={clearingLogs}
          handleClearLogs={handleClearLogs}
          terminalEndRef={terminalEndRef}
        />

      </div>

      {/* Toast popup */}
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'info' })}
      />
    </div>
  );
}
