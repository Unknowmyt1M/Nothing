'use client';

import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          padding: '40px 20px',
          textAlign: 'center',
        }}>
          <div style={{
            width: '80px',
            height: '80px',
            borderRadius: '50%',
            background: 'rgba(255, 0, 127, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '24px',
          }}>
            <span style={{ fontSize: '36px' }}>&#9888;</span>
          </div>
          <h2 style={{
            fontSize: '22px',
            fontWeight: '700',
            color: 'var(--color-text-primary)',
            marginBottom: '12px',
          }}>
            Something went wrong
          </h2>
          <p style={{
            fontSize: '15px',
            color: 'var(--color-text-secondary)',
            maxWidth: '420px',
            lineHeight: '1.6',
            marginBottom: '24px',
          }}>
            An unexpected error occurred. Please try refreshing the page.
          </p>
          <button
            className="btn-cyber"
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            style={{
              padding: '12px 32px',
              fontSize: '14px',
            }}
          >
            Reload Page
          </button>
          {this.state.error && (
            <pre style={{
              marginTop: '20px',
              padding: '16px',
              background: 'rgba(255, 0, 127, 0.05)',
              border: '1px solid rgba(255, 0, 127, 0.15)',
              borderRadius: '8px',
              color: 'var(--color-text-muted)',
              fontSize: '12px',
              fontFamily: 'var(--font-mono)',
              maxWidth: '600px',
              overflow: 'auto',
              whiteSpace: 'pre-wrap',
            }}>
              {this.state.error.message}
            </pre>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}
