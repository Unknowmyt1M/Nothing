import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Toast from '@/components/Toast';
import UrlInput from './UrlInput';
import MetadataCard from './MetadataCard';
import DownloadConsole from './DownloadConsole';
import YoutubeUploader from './YoutubeUploader';
import ErrorDisplay from './ErrorDisplay';

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

  // Error state — structured error object from backend
  const [error, setError] = useState(null);

  // Toast notifications
  const [toast, setToast] = useState({ message: '', type: 'info' });

  const downloadEsRef = useRef(null);
  const uploadEsRef = useRef(null);
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || '';

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
        } else {
          setPlatformInfo({ platform: 'unknown', display_name: '', supported: false });
        }
      })
      .catch((err) => console.error('Platform check failed:', err));
    }, 400);

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
    setTimeout(() => {
      setToast({ message: '', type: 'info' });
    }, type === 'error' ? 6000 : 4000);
  };

  // Parse structured error from backend response
  const parseError = (data) => {
    if (data.error === true || data.error_code) {
      return {
        code: data.code || data.error_code || 'UNKNOWN_ERROR',
        title: data.title || 'Something went wrong',
        message: data.message || 'An unexpected error occurred.',
        suggestion: data.suggestion || '',
        retryable: data.retryable !== false,
        details: data.details || '',
      };
    }
    return null;
  };

  const handleExtract = useCallback((e) => {
    if (e) e.preventDefault();
    if (!url.trim()) return;

    setExtracting(true);
    setMetadata(null);
    setQualities([]);
    setSelectedQuality('');
    setDownloaded(false);
    setUploaded(false);
    setError(null);

    fetch('/api/downloader/extract_metadata', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    })
    .then((res) => res.json())
    .then((data) => {
      const structuredErr = parseError(data);
      if (structuredErr) {
        setError(structuredErr);
        setExtracting(false);
        return;
      }
      setMetadata(data);
      triggerToast('Metadata extracted successfully!', 'success');

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
      .catch(() => setFetchingQualities(false));
    })
    .catch((err) => {
      setError({
        code: 'NETWORK_ERROR',
        title: 'Connection problem',
        message: err.message || 'Could not reach the server.',
        suggestion: 'Check your internet connection and try again.',
        retryable: true,
      });
    })
    .finally(() => {
      setExtracting(false);
    });
  }, [url]);

  const handleDownload = useCallback(() => {
    if (!selectedQuality) {
      triggerToast('Please select a quality format', 'error');
      return;
    }

    setDownloading(true);
    setDownloadProgress({ progress: 0, status: 'Starting download...' });
    setError(null);

    fetch('/api/downloader/download_video', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, quality: selectedQuality })
    })
    .then((res) => res.json())
    .then((data) => {
      const structuredErr = parseError(data);
      if (structuredErr) {
        setError(structuredErr);
        setDownloading(false);
        return;
      }

      const dlId = data.download_id;
      setDownloadId(dlId);

      if (downloadEsRef.current) downloadEsRef.current.close();
      const es = new EventSource(`${backendUrl}/api/downloader/progress/${dlId}`);
      downloadEsRef.current = es;

      es.onmessage = (event) => {
        const progressData = JSON.parse(event.data);
        setDownloadProgress(progressData);

        if (progressData.status === 'completed') {
          es.close();
          setDownloading(false);
          setDownloaded(true);
          triggerToast('Video downloaded to local server!', 'success');
        } else if (progressData.status === 'error') {
          es.close();
          setDownloading(false);
          setError({
            code: progressData.error_code || 'DOWNLOAD_ERROR',
            title: 'Download failed',
            message: progressData.error || 'An error occurred during download.',
            suggestion: progressData.error_suggestion || 'Try again or select a different quality.',
            retryable: true,
            details: '',
          });
        } else if (progressData.status === 'cancelled') {
          es.close();
          setDownloading(false);
          triggerToast('Download cancelled.', 'info');
        }
      };

      es.onerror = () => {
        es.close();
        setDownloading(false);
        setError({
          code: 'NETWORK_ERROR',
          title: 'Lost connection',
          message: 'Lost connection to the progress stream.',
          suggestion: 'The download may still be running. Try refreshing.',
          retryable: true,
        });
      };
    })
    .catch((err) => {
      setDownloading(false);
      setError({
        code: 'NETWORK_ERROR',
        title: 'Connection problem',
        message: err.message || 'Could not reach the server.',
        retryable: true,
      });
    });
  }, [url, selectedQuality, backendUrl]);

  const handleCancelDownload = useCallback(() => {
    if (!downloadId) return;
    fetch(`/api/downloader/cancel_download/${downloadId}`, { method: 'POST' })
      .then(() => triggerToast('Cancel request sent', 'info'))
      .catch(() => triggerToast('Could not cancel download', 'error'));
  }, [downloadId]);

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
      const structuredErr = parseError(data);
      if (structuredErr) {
        setError(structuredErr);
        setUploading(false);
        return;
      }

      const upId = data.upload_id;
      setUploadId(upId);

      if (uploadEsRef.current) uploadEsRef.current.close();
      const es = new EventSource(`${backendUrl}/api/downloader/upload_progress/${upId}`);
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
          setError({
            code: progressData.error_code || 'DOWNLOAD_ERROR',
            title: 'Upload failed',
            message: progressData.error || 'An error occurred during upload.',
            suggestion: 'Check your YouTube connection and try again.',
            retryable: true,
          });
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

  const handleDismissError = () => setError(null);

  return (
    <div className="animate-fade-in extraction-portal">
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

      {/* Structured error display */}
      <AnimatePresence>
        {error && (
          <div className="error-display-container">
            <ErrorDisplay
              error={error}
              onRetry={error.retryable ? (error.code?.includes('METADATA') || error.code === 'EXTRACTION_ERROR' ? handleExtract : handleDownload) : undefined}
              onDismiss={handleDismissError}
            />
          </div>
        )}
      </AnimatePresence>

      {/* Metadata card with actions console */}
      <AnimatePresence>
        {metadata && (
          <MetadataCard
            metadata={metadata}
            setMetadata={setMetadata}
            triggerToast={triggerToast}
          >
            <DownloadConsole
              downloading={downloading}
              downloaded={downloaded}
              fetchingQualities={fetchingQualities}
              qualities={qualities}
              selectedQuality={selectedQuality}
              setSelectedQuality={setSelectedQuality}
              downloadProgress={downloadProgress}
              handleDownload={handleDownload}
              onCancel={handleCancelDownload}
              downloadId={downloadId}
            />

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
