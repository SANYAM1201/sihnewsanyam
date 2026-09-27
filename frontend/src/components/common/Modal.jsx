import React, { useEffect } from 'react';

export default function Modal({ isOpen, onClose, title, children, maxWidth = '650px' }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen && onClose) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.65)',
        backdropFilter: 'blur(3px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'var(--gesso-canvas, #ffffff)',
          color: 'var(--gesso-fg, #1a1a1a)',
          borderRadius: '12px',
          width: '100%',
          maxWidth,
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 40px rgba(0,0,0,0.3)',
          overflow: 'hidden',
          border: '1px solid var(--gesso-surface-elevated, #dedcde)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderBottom: '1px solid var(--gesso-divider, rgba(0,0,0,0.08))',
            background: 'var(--gesso-surface, #f4f2f6)',
          }}
        >
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>{title}</h3>
          <button
            onClick={onClose}
            style={{
              fontSize: '18px',
              padding: '4px 8px',
              borderRadius: '4px',
              cursor: 'pointer',
              color: 'var(--gesso-fg-muted)',
            }}
          >
            ✕
          </button>
        </div>
        <div style={{ padding: '20px', overflowY: 'auto' }}>
          {children}
        </div>
      </div>
    </div>
  );
}
