import React from 'react';
import { NavLink } from 'react-router-dom';
import './Sidebar.css';

const NAV_ITEMS = [
  { path: '/', label: 'Main Dashboard', icon: '📊' },
  { path: '/live-survey', label: 'Live Survey', icon: '📡' },
  { path: '/map', label: 'Swath Map', icon: '🗺️' },
  { path: '/anomalies', label: 'Anomaly Inspector', icon: '🔍' },
  { path: '/reports', label: 'Reports & Export', icon: '📑' },
  { path: '/health', label: 'System Health', icon: '🩺' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
  { path: '/api-docs', label: 'API Docs', icon: '📖' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <div className="sidebar__logo-badge">SS</div>
        <div className="sidebar__brand-text">
          <h2>SONAR SENTRY</h2>
          <p>SIH 2026 · NIOT / MoES</p>
        </div>
      </div>

      <nav className="sidebar__nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `sidebar__item ${isActive ? 'active' : ''}`
            }
          >
            <span className="sidebar__icon">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar__footer">
        <div><strong>Mission:</strong> MSN-3D02</div>
        <div><strong>Vessel:</strong> Sagar Nidhi</div>
        <div><strong>Status:</strong> Ready</div>
      </div>
    </aside>
  );
}
