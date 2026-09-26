// src/components/Navbar.jsx
import { useNavigate, useLocation } from 'react-router-dom'

function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()

  const isActive = (paths) => paths.some((p) => location.pathname.startsWith(p))

  const navItems = [
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'Operations', path: '/receipts', matchPaths: ['/receipts', '/delivery'] },
    { label: 'Products', path: '/products' },
    { label: 'Move History', path: '/move-history' },
    { label: 'Settings', path: '/settings/warehouse', matchPaths: ['/settings'] },
  ]

  return (
    <div style={styles.navbar}>
      <div style={styles.navLinks}>
        {navItems.map((item) => (
          <span
            key={item.label}
            onClick={() => navigate(item.path)}
            style={{
              ...styles.navItem,
              ...(isActive(item.matchPaths || [item.path]) ? styles.navItemActive : {}),
            }}
          >
            {item.label}
          </span>
        ))}
      </div>
      <div style={styles.profileIcon} onClick={() => navigate('/login')} title="Logout">
        A
      </div>
    </div>
  )
}

const styles = {
  navbar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: '12px 24px',
    borderBottom: '1px solid #ddd',
  },
  navLinks: {
    display: 'flex',
    gap: '24px',
  },
  navItem: {
    fontSize: '14px',
    color: '#555',
    cursor: 'pointer',
  },
  navItemActive: {
    color: '#2563eb',
    fontWeight: 'bold',
  },
  profileIcon: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    backgroundColor: '#2563eb',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '14px',
    cursor: 'pointer',
  },
}

export default Navbar