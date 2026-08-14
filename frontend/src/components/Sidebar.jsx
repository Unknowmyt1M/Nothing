'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';

export default function Sidebar() {
  const pathname = usePathname();
  const [authStatus, setAuthStatus] = useState({ authenticated: false, user: null });
  const [loading, setLoading] = useState(true);

  // Fetch authentication status on mount
  useEffect(() => {
    fetch('/api/auth/status')
      .then((res) => res.json())
      .then((data) => {
        setAuthStatus(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch auth status:', err);
        setLoading(false);
      });
  }, [pathname]); // Refetch on route changes to keep status fresh

  const menuItems = [
    { name: 'Download Hub', path: '/', icon: 'fa-solid fa-cloud-arrow-down' },
    { name: 'Integrations', path: '/accounts', icon: 'fa-solid fa-user-gear' },
    { name: 'Auto Monitor', path: '/automation', icon: 'fa-solid fa-circle-nodes' },
    { name: 'Platforms', path: '/platforms', icon: 'fa-solid fa-layer-group' },
    { name: 'Metadata Hub', path: '/metadata', icon: 'fa-solid fa-terminal' }
  ];

  return (
    <aside className="glass-panel" style={{
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
            cursor: 'pointer'
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
            textShadow: '0 0 10px rgba(0, 242, 254, 0.15)'
          }}>UPDOWNVID</h1>
          <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', letterSpacing: '2px', textTransform: 'uppercase' }}>V2.0 Console</span>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px', position: 'relative' }}>
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
                transition: 'color 0.3s ease'
              }}
            >
              {/* Sliding Indicator */}
              {isActive && (
                <motion.div
                  layoutId="activeNavIndicator"
                  style={{
                    position: 'absolute',
                    inset: 0,
                    borderRadius: '10px',
                    background: 'linear-gradient(135deg, rgba(0, 242, 254, 0.08) 0%, rgba(138, 43, 226, 0.08) 100%)',
                    border: '1px solid rgba(0, 242, 254, 0.25)',
                    boxShadow: 'inset 0 0 8px rgba(0, 242, 254, 0.05), 0 4px 15px rgba(0, 242, 254, 0.05)',
                    zIndex: 0
                  }}
                  transition={{ type: 'spring', stiffness: 350, damping: 25 }}
                />
              )}

              {/* Hover Glow Effect */}
              <motion.div 
                className="sidebar-hover-glow"
                whileHover={{ opacity: 0.15 }}
                style={{
                  position: 'absolute',
                  inset: 0,
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, var(--color-cyan) 0%, var(--color-purple) 100%)',
                  opacity: 0,
                  zIndex: 0,
                  transition: 'opacity 0.2s ease'
                }}
              />

              <i className={item.icon} style={{ 
                fontSize: '16px',
                color: isActive ? 'var(--color-cyan)' : 'var(--color-text-muted)',
                filter: isActive ? 'drop-shadow(0 0 6px var(--color-cyan))' : 'none',
                position: 'relative',
                zIndex: 1,
                transition: 'color 0.3s ease, filter 0.3s ease'
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
            <motion.div 
              whileHover={{ scale: 1.08 }}
              style={{ position: 'relative', cursor: 'pointer' }}
            >
              <img 
                src={authStatus.user?.picture || 'https://www.gravatar.com/avatar?d=mp'} 
                alt="User Avatar"
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
            </motion.div>
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
            <div style={{ position: 'relative' }}>
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
    </aside>
  );
}
