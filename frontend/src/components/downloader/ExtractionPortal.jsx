import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Toast from '@/components/Toast';
import UrlInput from './UrlInput';
import MetadataCard from './MetadataCard';
import DownloadConsole from './DownloadConsole';
import YoutubeUploader from './YoutubeUploader';

export default function ExtractionPortal() {
  const [url, setUrl] = useState('');
  const [platformInfo, setPlatformInfo] = useState({ platform: 'unknown', display_name: '', supported: false });
  const [extracting, setExtracting] = useState(false);
  const [metadata, setMetadata] = useState(null);
  
  // Quality options
  const [qualities, setQualities] = useState([]);
  const [selectedQuality, setSelectedQuality] = useState('');
  const [fetchingQualities, setFetchingQualities] = useState(false);
  
  // Download states
  const [downloading, setDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(null);
  const [downloadId, setDownloadId] = useState(null);
  const [downloaded, setDownloaded] = useState(false);
  
  // Upload states
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(null);
  const [uploadId, setUploadId] = useState(null);
  const [uploaded, setUploaded] = useState(false);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [privacy, setPrivacy] = useState('public');
  
  // Toast notifications
  const [toast, setToast] = useState({ message: '', type: 'info' });
  
  const downloadEsRef = useRef(null);
  const uploadEsRef = useRef(null);

  // Auto-detect platform on URL changes
  useEffect(() => {
    if (!url.trim()) {
      const timer = setTimeout(() => {
        setPlatformInfo({ platform: 'unknown', display_name: '', supported: false });
      }, 0);
      return () => clearTimeout(timer);
    }
    
    const timeout = setTimeout(() => {
      fetch('/api/downloader/detect_platform', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      })
      .then((res) => res.json())
      .then((data) => {
        if (!data.error) {
          setPlatformInfo(data);
        }
      })
      .catch((err) => console.error('Platform check failed:', err));
    }, 400); // Debounce API requests
    
    return () => clearTimeout(timeout);
  }, [url]);

  // Clean up SSE connections on unmount
  useEffect(() => {
    return () => {
      if (downloadEsRef.current) downloadEsRef.current.close();
      if (uploadEsRef.current) uploadEsRef.current.close();
    };
  }, []);

  const triggerToast = (message, type = 'info') => {
    setToast({ message, type });
    // Auto hide after 4 seconds
    setTimeout(() => {
      setToast({ message: '', type: 'info' });
    }, 4000);
  };

  const handleExtract = (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    
    setExtracting(true);
    setMetadata(null);
    setQualities([]);
    setSelectedQuality('');
    setDownloaded(false);
    setUploaded(false);
    
    fetch('/api/downloader/extract_metadata', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) throw new Error(data.error);
      setMetadata(data);
      triggerToast('Metadata extracted successfully!', 'success');
      
      // Fetch available download qualities
      setFetchingQualities(true);
      fetch('/api/downloader/get_video_qualities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      })
      .then((res) => res.json())
      .then((qData) => {
        if (qData.qualities) {
          setQualities(qData.qualities);
          if (qData.qualities.length > 0) {
            setSelectedQuality(qData.qualities[0].format_id);
          }
        }
        setFetchingQualities(false);
      })
      .catch((err) => {
        console.error('Error fetching qualities:', err);
        setFetchingQualities(false);
      });
    })
    .catch((err) => {
      triggerToast(err.message, 'error');
    })
    .finally(() => {
      setExtracting(false);
    });
  };

  const handleDownload = () => {
    if (!selectedQuality) {
      triggerToast('Please select a quality format', 'error');
      return;
    }
    
    setDownloading(true);
    setDownloadProgress({ progress: 0, status: 'Starting download...' });
    
    fetch('/api/downloader/download_video', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, quality: selectedQuality })
    })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) throw new Error(data.error);
      
      const dlId = data.download_id;
      setDownloadId(dlId);
      
      // Subscribe to Server-Sent Events (SSE) for progress streaming (updated to port 3000)
      if (downloadEsRef.current) downloadEsRef.current.close();
      
      const backendBaseUrl = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:3000` : 'http://localhost:3000';
      const es = new EventSource(`${backendBaseUrl}/api/downloader/progress/${dlId}`);
      downloadEsRef.current = es;
      
      es.onmessage = (event) => {
        const progressData = JSON.parse(event.data);
        setDownloadProgress(progressData);
        
        if (progressData.status === 'completed') {
          es.close();
          setDownloading(false);
          setDownloaded(true);
          triggerToast('Video downloaded to local server successfully!', 'success');
        } else if (progressData.status === 'error') {
          es.close();
          setDownloading(false);
          triggerToast(`Download failed: ${progressData.error}`, 'error');
        }
      };
      
      es.onerror = () => {
        es.close();
        setDownloading(false);
        triggerToast('Lost connection to progress stream', 'error');
      };
    })
    .catch((err) => {
      setDownloading(false);
      triggerToast(err.message, 'error');
    });
  };

  const handleUpload = () => {
    setUploading(true);
    setUploadProgress({ progress: 50, status: 'Preparing upload...' });
    
    const bodyData = {
      url,
      title: metadata.title,
      description: metadata.description,
      tags: metadata.tags.join(','),
      privacy
    };
    
    fetch('/api/downloader/upload_video', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyData)
    })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) throw new Error(data.error);
      
      const upId = data.upload_id;
      setUploadId(upId);
      
      if (uploadEsRef.current) uploadEsRef.current.close();
      
      const backendBaseUrl = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:3000` : 'http://localhost:3000';
      const es = new EventSource(`${backendBaseUrl}/api/downloader/upload_progress/${upId}`);
      uploadEsRef.current = es;
      
      es.onmessage = (event) => {
        const progressData = JSON.parse(event.data);
        setUploadProgress(progressData);
        
        if (progressData.status === 'completed') {
          es.close();
          setUploading(false);
          setUploaded(true);
          setYoutubeUrl(progressData.youtube_url);
          triggerToast('Uploaded to YouTube successfully!', 'success');
        } else if (progressData.status === 'error') {
          es.close();
          setUploading(false);
          triggerToast(`Upload failed: ${progressData.error}`, 'error');
        }
      };
      
      es.onerror = () => {
        es.close();
        setUploading(false);
        triggerToast('Lost connection to upload progress stream', 'error');
      };
    })
    .catch((err) => {
      setUploading(false);
      triggerToast(err.message, 'error');
    });
  };

  return (
    <div className="animate-fade-in" style={{ maxWidth: '1000px', margin: '0 auto', width: '100%' }}>
      {/* Title */}
      <div style={{ marginBottom: '35px' }}>
        <motion.h2 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          style={{ fontSize: '32px', fontWeight: '800', background: 'linear-gradient(to right, #00f2fe, #ff007f)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginBottom: '8px' }}
        >
          EXTRACTION PORTAL
        </motion.h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '15px' }}>
          Paste a video URL from any platform to extract high quality formats or automate upload pipelines.
        </p>
      </div>

      {/* Input panel */}
      <UrlInput 
        url={url}
        setUrl={setUrl}
        platformInfo={platformInfo}
        extracting={extracting}
        handleExtract={handleExtract}
      />

      {/* Metadata card with actions console */}
      <AnimatePresence>
        {metadata && (
          <MetadataCard 
            metadata={metadata} 
            setMetadata={setMetadata} 
            triggerToast={triggerToast}
          >
            {/* Download Console */}
            <DownloadConsole 
              downloading={downloading}
              downloaded={downloaded}
              fetchingQualities={fetchingQualities}
              qualities={qualities}
              selectedQuality={selectedQuality}
              setSelectedQuality={setSelectedQuality}
              downloadProgress={downloadProgress}
              handleDownload={handleDownload}
            />

            {/* YouTube Uploader */}
            <YoutubeUploader 
              downloaded={downloaded}
              uploading={uploading}
              uploaded={uploaded}
              privacy={privacy}
              setPrivacy={setPrivacy}
              uploadProgress={uploadProgress}
              youtubeUrl={youtubeUrl}
              handleUpload={handleUpload}
            />
          </MetadataCard>
        )}
      </AnimatePresence>

      {/* Toast notifications */}
      <Toast 
        message={toast.message} 
        type={toast.type} 
        onClose={() => setToast({ message: '', type: 'info' })} 
      />
    </div>
  );
}
