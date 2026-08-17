import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Toast from '@/components/Toast';
import CookieHealthCard from './CookieHealthCard';
import DiagnosticsConsole from './DiagnosticsConsole';

export default function DiagnosticsHub() {
  const [cookieStatus, setCookieStatus] = useState(null);
  const [loadingCookies, setLoadingCookies] = useState(true);
  
  // Sandbox metadata state
  const [sandboxUrl, setSandboxUrl] = useState('');
  const [extracting, setExtracting] = useState(false);
  const [extractedData, setExtractedData] = useState(null);

  // Toast notifications
  const [toast, setToast] = useState({ message: '', type: 'info' });

  const triggerToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast({ message: '', type: 'info' });
    }, 4500);
  };

  const fetchCookieStatus = async () => {
    try {
      const res = await fetch('/api/debug/check_cookies');
      const data = await res.json();
      setCookieStatus(data);
    } catch (err) {
      console.error('Failed to fetch cookie status:', err);
    } finally {
      setLoadingCookies(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchCookieStatus();
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  const handleDiagnose = async (e) => {
    e.preventDefault();
    if (!sandboxUrl.trim()) return;

    setExtracting(true);
    setExtractedData(null);

    try {
      const res = await fetch('/api/debug/test_metadata', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: sandboxUrl })
      });
      const data = await res.json();
      if (data.error) {
        throw new Error(data.error);
      }
      setExtractedData(data);
      triggerToast('Diagnostics completed successfully!', 'success');
    } catch (err) {
      triggerToast(err.message, 'error');
    } finally {
      setExtracting(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ maxWidth: '1100px', margin: '0 auto', width: '100%' }}>
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
          METADATA & DIAGNOSTICS HUB
        </motion.h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '15px' }}>
          Inspect browser bypass cookies, test metadata parser nodes, and extract deep technical video specs.
        </p>
      </div>

      <div className="diagnostics-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1.3fr', gap: '30px', alignItems: 'start' }}>
        
        {/* Left Column: Cookie status & instructions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
          
          {/* Cookies Health monitor */}
          <CookieHealthCard 
            loadingCookies={loadingCookies}
            cookieStatus={cookieStatus}
          />

          {/* Guide Card */}
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-panel" 
            style={{ padding: '25px', background: 'rgba(0, 242, 254, 0.01)', border: '1px solid rgba(0, 242, 254, 0.1)' }}
          >
            <h4 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--color-cyan)', marginBottom: '10px' }}>
              💡 Cookie Injection Guide
            </h4>
            <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', lineHeight: '1.6' }}>
              If you receive extraction block or bot-rate-limit errors from social media platforms, place Netscape format cookies in the relative directories (e.g. <code style={{ color: '#fff' }}>cookies/youtube.txt</code>) to bypass access barriers.
            </p>
          </motion.div>
        </div>

        {/* Right Column: Sandbox Tester & Monospaced JSON Output */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', height: '100%' }}>
          <DiagnosticsConsole 
            sandboxUrl={sandboxUrl}
            setSandboxUrl={setSandboxUrl}
            extracting={extracting}
            extractedData={extractedData}
            handleDiagnose={handleDiagnose}
          />
        </div>

      </div>

      {/* Notifications toast */}
      <Toast 
        message={toast.message} 
        type={toast.type} 
        onClose={() => setToast({ message: '', type: 'info' })} 
      />
    </div>
  );
}
