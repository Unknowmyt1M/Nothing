'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { supabase } from '@/lib/supabaseClient';

export default function Sidebar() {
  const pathname = usePathname();
  const [authStatus, setAuthStatus] = useState({ authenticated: false, user: null });
  const [loading, setLoading] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Check Supabase session first
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.access_token) {
          // Sync with backend to get full user data
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
            setLoading(false);
            return;
          }
        }
        // Fallback to backend session
        const res = await fetch('/api/auth/status');
        const data = await res.json();
        setAuthStatus(data);
      } catch {
        setAuthStatus({ authenticated: false, user: null });
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, [pathname]);

  // Auto-close drawer on navigation
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  // Lock body scroll when drawer open
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  const closeMobile = useCallback(() => setMobileOpen(false), []);

  const menuItems = [
    { name: 'Download Hub', path: '/', icon: 'fa-solid fa-cloud-arrow-down' },
    { name: 'Integrations', path: '/accounts', icon: 'fa-solid fa-user-gear' },
    { name: 'Auto Monitor', path: '/automation', icon: 'fa-solid fa-circle-nodes' },
    { name: 'Analytics', path: '/analytics', icon: 'fa-solid fa-chart-line' },
    { name: 'Platforms', path: '/platforms', icon: 'fa-solid fa-layer-group' },
    { name: 'Metadata Hub', path: '/metadata', icon: 'fa-solid fa-terminal' }
  ];

  const sidebarContent = (
    <>
      {/* Brand Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        marginBottom: '40px',
        padding: '0 5px'
      }}>
        <motion.div
          whileHover={{ scale: 1.1, rotate: 10 }}
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, var(--color-cyan) 0%, var(--color-purple) 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--neon-shadow-cyan)',
            cursor: 'pointer',
            flexShrink: 0,
          }}
        >
          <i className="fa-solid fa-bolt" style={{ color: '#000000', fontSize: '18px' }}></i>
        </motion.div>
        <div>
          <h1 style={{
            fontSize: '18px',
            fontWeight: '800',
            letterSpacing: '1.5px',
            background: 'linear-gradient(to right, #00f2fe, #ff007f)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>UPDOWNVID</h1>
          <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', letterSpacing: '2px', textTransform: 'uppercase' }}>V2.0 Console</span>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {menuItems.map((item) => {
          const isActive = pathname === item.path;
          return (
            <Link
              key={item.path}
              href={item.path}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                padding: '12px 16px',
                borderRadius: '10px',
                color: isActive ? '#ffffff' : 'var(--color-text-secondary)',
                textDecoration: 'none',
                fontSize: '14px',
                fontWeight: isActive ? '600' : '400',
                position: 'relative',
                transition: 'color 0.3s ease',
                minHeight: '44px',
              }}
            >
              {isActive && (
                <motion.div
                  layoutId="activeNavIndicator"
                  style={{
                    position: 'absolute',
                    inset: 0,
                    borderRadius: '10px',
                    background: 'linear-gradient(135deg, rgba(0, 242, 254, 0.08) 0%, rgba(138, 43, 226, 0.08) 100%)',
                    border: '1px solid rgba(0, 242, 254, 0.25)',
                    zIndex: 0,
                  }}
                  transition={{ type: 'spring', stiffness: 350, damping: 25 }}
                />
              )}
              <i className={item.icon} style={{
                fontSize: '16px',
                color: isActive ? 'var(--color-cyan)' : 'var(--color-text-muted)',
                filter: isActive ? 'drop-shadow(0 0 6px var(--color-cyan))' : 'none',
                position: 'relative',
                zIndex: 1,
                width: '20px',
                textAlign: 'center',
              }}></i>
              <span style={{ position: 'relative', zIndex: 1 }}>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* User profile footer */}
      <div style={{
        paddingTop: '20px',
        borderTop: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      }}>
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--color-text-muted)', fontSize: '12px' }}>
            <i className="fa-solid fa-circle-notch fa-spin"></i>
            <span>Checking auth...</span>
          </div>
        ) : authStatus.authenticated ? (
          <>
            <div style={{ position: 'relative', flexShrink: 0 }}>
              <img
                src={authStatus.user?.picture || 'https://www.gravatar.com/avatar?d=mp'}
                alt="User Avatar"
                onError={(e) => { e.target.src = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="38" height="38" viewBox="0 0 38 38"><rect width="38" height="38" rx="19" fill="%2312101f"/><text x="19" y="24" text-anchor="middle" fill="%2300f2fe" font-size="18" font-family="sans-serif">U</text></svg>'); }}
                style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '50%',
                  border: '1.5px solid var(--color-cyan)',
                  boxShadow: 'var(--neon-shadow-cyan)'
                }}
              />
              <span style={{
                position: 'absolute',
                bottom: '0',
                right: '0',
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: '#2ecc71',
                border: '2px solid var(--bg-primary)',
                animation: 'pulseGreen 1.5s infinite',
                boxShadow: '0 0 8px #2ecc71'
              }}></span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <span style={{ fontSize: '13px', fontWeight: '600', color: '#ffffff', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                {authStatus.user?.name}
              </span>
              <span style={{ fontSize: '10px', color: 'var(--color-cyan)', fontWeight: '600', letterSpacing: '0.5px' }}>
                ONLINE
              </span>
            </div>
          </>
        ) : (
          <>
            <div style={{ position: 'relative', flexShrink: 0 }}>
              <div style={{
                width: '38px',
                height: '38px',
                borderRadius: '50%',
                background: 'rgba(255, 255, 255, 0.05)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid var(--color-border)'
              }}>
                <i className="fa-solid fa-user-secret" style={{ color: 'var(--color-text-muted)' }}></i>
              </div>
              <span style={{
                position: 'absolute',
                bottom: '0',
                right: '0',
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: 'var(--color-pink)',
                border: '2px solid var(--bg-primary)',
                boxShadow: '0 0 6px var(--color-pink)'
              }}></span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '13px', fontWeight: '500', color: 'var(--color-text-secondary)' }}>Guest User</span>
              <span style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>Console Locked</span>
            </div>
          </>
        )}
      </div>
    </>
  );

  return (
    <>
      {/* Mobile Hamburger Button */}
      <button
        className="sidebar-hamburger"
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label="Toggle navigation menu"
      >
        <i className={`fa-solid ${mobileOpen ? 'fa-xmark' : 'fa-bars'}`}></i>
      </button>

      {/* Desktop Sidebar */}
      <aside className="sidebar-desktop glass-panel" style={{
        position: 'fixed',
        left: '20px',
        top: '20px',
        bottom: '20px',
        width: '240px',
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        padding: '30px 20px',
        background: 'var(--bg-sidebar)',
        borderColor: 'var(--color-border)',
        boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.5)'
      }}>
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            className="sidebar-mobile-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={closeMobile}
          />
        )}
      </AnimatePresence>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.aside
            className="sidebar-mobile-drawer glass-panel"
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', stiffness: 350, damping: 30 }}
            style={{
              position: 'fixed',
              left: 0,
              top: 0,
              bottom: 0,
              width: '280px',
              maxWidth: '85vw',
              zIndex: 200,
              display: 'flex',
              flexDirection: 'column',
              padding: '24px 20px',
              background: 'var(--bg-sidebar)',
              borderColor: 'var(--color-border)',
              boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.7)',
              overflowY: 'auto',
            }}
          >
            {sidebarContent}
          </motion.aside>
        )}
      </AnimatePresence>
    </>
  );
}
