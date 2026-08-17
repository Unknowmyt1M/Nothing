import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import Toast from '@/components/Toast';
import GoogleLinkCard from './GoogleLinkCard';
import AdvancedSettingsForm from './AdvancedSettingsForm';
import { supabase } from '@/lib/supabaseClient';

export default function IntegrationsHub() {
  const router = useRouter();
  const [authStatus, setAuthStatus] = useState({ authenticated: false, user: null, youtube_channel: null });
  const [loading, setLoading] = useState(true);
  
  // Settings Form State
  const [apiKey, setApiKey] = useState('');
  const [monitorInterval, setMonitorInterval] = useState(300);
  const [savingSettings, setSavingSettings] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  // Toast State
  const [toast, setToast] = useState({ message: '', type: 'info' });

  const triggerToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast({ message: '', type: 'info' });
    }, 4500);
  };

  // Fetch authentication status and settings
  const fetchData = async () => {
    setLoading(true);
    try {
      // First check Supabase session
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session?.access_token) {
        // Sync with backend
        try {
          const syncRes = await fetch('/api/auth/supabase_sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ supabase_access_token: session.access_token }),
          });
          const syncData = await syncRes.json();
          if (syncData.success) {
            setAuthStatus({
              authenticated: true,
              user: syncData.user,
              youtube_channel: syncData.youtube_channel,
            });
            // Fetch settings
            const settingsRes = await fetch('/api/automation/get_settings');
            const settingsData = await settingsRes.json();
            if (!settingsData.error) {
              setApiKey(settingsData.api_key || '');
              setMonitorInterval(settingsData.monitor_interval || 300);
            }
            setLoading(false);
            return;
          }
        } catch (syncErr) {
          console.error('Backend sync failed:', syncErr);
        }
      }

      // Fallback: check backend session (backward compatibility)
      const authRes = await fetch('/api/auth/status');
      const authData = await authRes.json();
      setAuthStatus(authData);

      if (authData.authenticated) {
        const settingsRes = await fetch('/api/automation/get_settings');
        const settingsData = await settingsRes.json();
        if (!settingsData.error) {
          setApiKey(settingsData.api_key || '');
          setMonitorInterval(settingsData.monitor_interval || 300);
        }
      }
    } catch (err) {
      console.error('Failed to fetch settings/status:', err);
      triggerToast('Error loading profile configuration', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchData();
    }, 0);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Parse callback URLs search params (success or errors)
  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const connected = searchParams.get('connected');
    const error = searchParams.get('error');

    if (connected === 'true') {
      const timer = setTimeout(() => {
        triggerToast('Google account successfully linked!', 'success');
      }, 0);
      // Clean query params
      router.replace('/accounts');
      return () => clearTimeout(timer);
    } else if (error) {
      const timer = setTimeout(() => {
        triggerToast(`Authentication Error: ${decodeURIComponent(error)}`, 'error');
      }, 0);
      router.replace('/accounts');
      return () => clearTimeout(timer);
    }
  }, [router]);

  // Handle Google login redirect
  const handleConnect = async () => {
    try {
      triggerToast('Redirecting to Google authentication...', 'info');
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          scopes: 'openid email profile https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtube.force-ssl https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/yt-analytics.readonly https://www.googleapis.com/auth/yt-analytics-monetary.readonly https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
          redirectTo: window.location.origin + '/accounts',
        },
      });
      if (error) throw error;
    } catch (err) {
      triggerToast(err.message, 'error');
    }
  };

  // Handle Logout/Disconnect
  const handleDisconnect = async () => {
    try {
      await supabase.auth.signOut();
      const res = await fetch('/api/auth/logout');
      const data = await res.json();
      if (data.success) {
        setAuthStatus({ authenticated: false, user: null, youtube_channel: null });
        setApiKey('');
        setMonitorInterval(300);
        triggerToast('Account disconnected successfully', 'info');
      } else {
        throw new Error(data.message || 'Logout failed');
      }
    } catch (err) {
      triggerToast(err.message, 'error');
    }
  };

  // Handle Settings Form Submit
  const handleSaveSettings = async (e) => {
    e.preventDefault();
    setSavingSettings(true);
    try {
      // Get existing settings to not overwrite everything
      const getRes = await fetch('/api/automation/get_settings');
      const currentSettings = await getRes.json();
      
      const payload = {
        ...currentSettings,
        api_key: apiKey,
        monitor_interval: parseInt(monitorInterval, 10) || 300
      };

      const saveRes = await fetch('/api/automation/save_settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await saveRes.json();
      if (data.success) {
        triggerToast('API credentials saved successfully!', 'success');
      } else {
        throw new Error(data.error || 'Failed to save settings');
      }
    } catch (err) {
      triggerToast(err.message, 'error');
    } finally {
      setSavingSettings(false);
    }
  };

  return (
    <div className="animate-fade-in hub-container" style={{ maxWidth: '900px', margin: '0 auto', width: '100%' }}>
      {/* Title */}
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
          INTEGRATIONS & SETTINGS
        </motion.h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '15px' }}>
          Connect your Google Accounts for YouTube publishing, and configure system API parameters.
        </p>
      </div>

      {loading ? (
        <div className="glass-panel" style={{ padding: '50px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '15px' }}>
          <i className="fa-solid fa-circle-notch fa-spin" style={{ fontSize: '32px', color: 'var(--color-cyan)' }}></i>
          <span style={{ color: 'var(--color-text-secondary)' }}>Loading account profiles...</span>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
          {/* Main Auth Integration Card */}
          <GoogleLinkCard 
            authStatus={authStatus}
            handleConnect={handleConnect}
            handleDisconnect={handleDisconnect}
          />

          {/* System Config / Developer Settings */}
          <AdvancedSettingsForm 
            authStatus={authStatus}
            apiKey={apiKey}
            setApiKey={setApiKey}
            monitorInterval={monitorInterval}
            setMonitorInterval={setMonitorInterval}
            savingSettings={savingSettings}
            showApiKey={showApiKey}
            setShowApiKey={setShowApiKey}
            handleSaveSettings={handleSaveSettings}
          />
        </div>
      )}

      {/* Notifications toast */}
      <Toast 
        message={toast.message} 
        type={toast.type} 
        onClose={() => setToast({ message: '', type: 'info' })} 
      />
    </div>
  );
}
