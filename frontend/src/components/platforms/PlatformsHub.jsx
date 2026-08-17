import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Toast from '@/components/Toast';
import SupportedPlatformsGrid from './SupportedPlatformsGrid';
import LinkCapabilityTester from './LinkCapabilityTester';

export default function PlatformsHub() {
  const [platforms, setPlatforms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  
  // URL Tester state
  const [testUrl, setTestUrl] = useState('');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  // Toast notifications
  const [toast, setToast] = useState({ message: '', type: 'info' });

  const triggerToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast({ message: '', type: 'info' });
    }, 4500);
  };

  const fetchPlatforms = async () => {
    try {
      const res = await fetch('/api/downloader/supported_platforms');
      const data = await res.json();
      if (data.platforms) {
        const excludeList = ['deadtoons', 'cybervynx', 'voe', 'filemoon', 'newerstream', 'shortic', 'smoothpre'];
        const filtered = data.platforms.filter(p => !excludeList.includes(p.id));
        setPlatforms(filtered);
      }
    } catch (err) {
      console.error('Failed to fetch platforms:', err);
      triggerToast('Error loading supported platforms list', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchPlatforms();
    }, 0);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleTestUrl = async (e) => {
    e.preventDefault();
    if (!testUrl.trim()) return;

    setTesting(true);
    setTestResult(null);

    try {
      const res = await fetch('/api/downloader/detect_platform', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: testUrl })
      });
      const data = await res.json();
      if (data.error) {
        throw new Error(data.error);
      }
      setTestResult(data);
      if (data.supported) {
        triggerToast('URL platform is supported and ready!', 'success');
      } else {
        triggerToast('This platform is not supported yet.', 'warning');
      }
    } catch (err) {
      triggerToast(err.message, 'error');
    } finally {
      setTesting(false);
    }
  };

  const filteredPlatforms = platforms.filter(p => 
    p.name.toLowerCase().includes(search.toLowerCase()) || 
    p.id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="animate-fade-in" style={{ maxWidth: '1000px', margin: '0 auto', width: '100%' }}>
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
          SUPPORTED VIDEO NETWORKS
        </motion.h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '15px' }}>
          Check our active parser configurations and verify URL compatibility for video extractions.
        </p>
      </div>

      <div className="platforms-grid" style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: '30px', alignItems: 'start' }}>
        
        {/* Left Column: Platforms List & Search */}
        <SupportedPlatformsGrid 
          loading={loading}
          search={search}
          setSearch={setSearch}
          filteredPlatforms={filteredPlatforms}
        />

        {/* Right Column: Dynamic URL support check form */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}
        >
          <LinkCapabilityTester 
            testUrl={testUrl}
            setTestUrl={setTestUrl}
            testing={testing}
            testResult={testResult}
            handleTestUrl={handleTestUrl}
          />
        </motion.div>

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
