// Global JavaScript functions and utilities

// Progress polling system
let progressPollingInterval = null;

function startProgressPolling(uploadId) {
    if (progressPollingInterval) {
        clearInterval(progressPollingInterval);
    }
    
    progressPollingInterval = setInterval(() => {
        fetch(`/upload_progress/${uploadId}`)
            .then(response => response.json())
            .then(data => {
                updateProgressDisplay(data);
                
                // Stop polling if completed or error
                if (data.status === 'completed' || data.status === 'error') {
                    clearInterval(progressPollingInterval);
                    progressPollingInterval = null;
                }
            })
            .catch(error => {
                console.error('Progress polling error:', error);
            });
    }, 1000); // Poll every second for real-time updates
}

function updateProgressDisplay(data) {
    const progressBar = document.querySelector('.progress-bar');
    const statusText = document.querySelector('#upload-status');
    const speedText = document.querySelector('#upload-speed');
    const etaText = document.querySelector('#upload-eta');
    const detailsText = document.querySelector('#upload-details');
    
    if (progressBar) {
        progressBar.style.width = `${data.progress || 0}%`;
        progressBar.textContent = `${Math.round(data.progress || 0)}%`;
    }
    
    if (statusText) {
        let statusMessage = '';
        if (data.status === 'downloading') {
            statusMessage = 'Downloading video...';
        } else if (data.status === 'uploading') {
            statusMessage = 'Uploading to YouTube...';
        } else if (data.status === 'completed') {
            statusMessage = 'Upload completed!';
        } else if (data.status === 'error') {
            statusMessage = `Error: ${data.error}`;
        }
        statusText.textContent = statusMessage;
    }
    
    if (speedText) {
        let speedDisplay = '';
        if (data.status === 'downloading' && data.speed) {
            speedDisplay = `Download Speed: ${data.speed}`;
        } else if (data.status === 'uploading' && data.upload_speed) {
            speedDisplay = `Upload Speed: ${data.upload_speed}`;
        }
        speedText.textContent = speedDisplay;
    }
    
    if (etaText) {
        let etaDisplay = '';
        if (data.status === 'downloading' && data.eta) {
            etaDisplay = `ETA: ${data.eta}`;
        } else if (data.status === 'uploading' && data.upload_eta) {
            etaDisplay = `ETA: ${data.upload_eta}`;
        }
        etaText.textContent = etaDisplay;
    }
    
    if (detailsText) {
        let details = '';
        if (data.status === 'downloading') {
            details = `Downloaded: ${data.downloaded || '0 B'} / ${data.total || 'Unknown'}`;
        } else if (data.status === 'uploading') {
            details = `Uploaded: ${data.uploaded || '0 B'} / ${data.total_upload || 'Unknown'}`;
        }
        detailsText.textContent = details;
    }
}

function stopProgressPolling() {
    if (progressPollingInterval) {
        clearInterval(progressPollingInterval);
        progressPollingInterval = null;
    }
}

// Toast notification system
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const iconClass = type === 'error' ? 'fas fa-exclamation-triangle text-danger' : 'fas fa-info-circle text-info';
    const bgClass = type === 'error' ? 'bg-danger' : 'bg-primary';
    
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="${iconClass} me-2"></i>
                <strong class="me-auto">${type === 'error' ? 'Error' : 'Info'}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', toastHTML);
    
    // Show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: type === 'error' ? 8000 : 5000
    });
    
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// Utility function to format file sizes
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Utility function to validate YouTube URLs
function isValidYouTubeUrl(url) {
    const pattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    return pattern.test(url);
}

// Copy to clipboard utility
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        return new Promise((resolve, reject) => {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                document.execCommand('copy');
                resolve();
            } catch (err) {
                reject(err);
            }
            
            document.body.removeChild(textArea);
        });
    }
}

// Progress bar animation utility
function animateProgressBar(element, targetPercentage, duration = 1000) {
    const startPercentage = parseFloat(element.style.width) || 0;
    const startTime = Date.now();
    
    function updateProgress() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const currentPercentage = startPercentage + (targetPercentage - startPercentage) * progress;
        
        element.style.width = currentPercentage + '%';
        element.textContent = Math.round(currentPercentage) + '%';
        
        if (progress < 1) {
            requestAnimationFrame(updateProgress);
        }
    }
    
    requestAnimationFrame(updateProgress);
}

// Form validation utilities
function validateForm(formElement) {
    const inputs = formElement.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        }
        
        // Special validation for URL inputs
        if (input.type === 'url' && input.value.trim()) {
            if (!isValidYouTubeUrl(input.value)) {
                input.classList.add('is-invalid');
                input.classList.remove('is-valid');
                isValid = false;
            }
        }
    });
    
    return isValid;
}

// Auto-clear validation states on input
document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('is-invalid') || e.target.classList.contains('is-valid')) {
            e.target.classList.remove('is-invalid', 'is-valid');
        }
    });
    
    // Add smooth transitions to progress bars
    const style = document.createElement('style');
    style.textContent = `
        .progress-bar {
            transition: width 0.3s ease-in-out;
        }
        
        .copy-btn:hover {
            transform: scale(1.1);
            transition: transform 0.2s ease-in-out;
        }
        
        .tag-copy-btn:hover {
            transform: scale(1.2);
            transition: transform 0.2s ease-in-out;
        }
    `;
    document.head.appendChild(style);
});

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showToast('An unexpected error occurred. Please try again.', 'error');
});

// Service worker registration (if available)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // This would register a service worker for offline functionality
        // navigator.serviceWorker.register('/sw.js');
    });
}
