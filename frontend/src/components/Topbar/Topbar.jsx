import { Link } from 'react-router-dom'
import styles from './Topbar.module.css'

const NAV_ITEMS = [
  { key: 'launch', label: 'Launch', to: '/' },
  { key: 'dashboard', label: 'Dashboard', to: '/dashboard' },
  { key: 'live-survey', label: 'Live Survey', to: '/live-survey' },
  { key: 'map', label: 'Map', to: '/map' },
  { key: 'anomalies', label: 'Anomalies', to: '/anomalies' },
  { key: 'reports', label: 'Reports', to: '/reports' },
  { key: 'uploads', label: 'Uploads', to: '/uploads' },
  { key: 'health', label: 'Health', to: '/health' },
  { key: 'settings', label: 'Settings', to: '/settings' },
]

export default function Topbar({ activePage = 'launch' }) {
  return (
    <header className={styles.topbar}>
      <div className={styles.topbar__brand}>
        <div className={styles.topbar__mark}>S</div>
        <div className={styles.topbar__text}>
          <span className={styles.topbar__label}>MoES · NIOT</span>
          <span className={styles.topbar__name}>SONAR SENTRY</span>
        </div>
      </div>

      <nav className={styles.topbar__nav}>
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.key}
            to={item.to}
            className={styles.topbar__navitem}
            aria-current={activePage === item.key ? 'page' : undefined}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <div className={styles.topbar__actions}>
        <div className={styles.statusPill}>
          <span className={styles.statusDot} />
          <span>PORT 8000</span>
        </div>
        <div className={styles.avatar}>NIOT</div>
      </div>
    </header>
  )
}
