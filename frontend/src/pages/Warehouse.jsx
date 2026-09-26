// src/pages/Warehouse.jsx
import { useState } from 'react'

function Warehouse() {
  const [warehouse, setWarehouse] = useState({
    name: '',
    shortCode: '',
    address: '',
  })

  const handleChange = (field, value) => {
    setWarehouse((prev) => ({ ...prev, [field]: value }))
  }

  const handleSave = () => {
    console.log('Warehouse saved:', warehouse)
    // TODO: connect to backend API
  }

  return (
    <div style={styles.page}>
      {/* Top Navbar */}
      <div style={styles.navbar}>
        <div style={styles.navLinks}>
          <span style={styles.navItem}>Dashboard</span>
          <span style={styles.navItem}>Operations</span>
          <span style={styles.navItem}>Products</span>
          <span style={styles.navItem}>Move History</span>
          <span style={{ ...styles.navItem, ...styles.navItemActive }}>Settings</span>
        </div>
        <div style={styles.profileIcon}>A</div>
      </div>

      {/* Main content */}
      <div style={styles.content}>
        <div style={styles.card}>
          <h2 style={styles.title}>Warehouse</h2>

          <div style={styles.field}>
            <label style={styles.label}>Name</label>
            <input
              style={styles.input}
              value={warehouse.name}
              onChange={(e) => handleChange('name', e.target.value)}
              placeholder="e.g. Main Warehouse"
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Short Code</label>
            <input
              style={styles.input}
              value={warehouse.shortCode}
              onChange={(e) => handleChange('shortCode', e.target.value)}
              placeholder="e.g. WH"
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Address</label>
            <textarea
              style={styles.textarea}
              value={warehouse.address}
              onChange={(e) => handleChange('address', e.target.value)}
              placeholder="Enter warehouse address"
              rows={4}
            />
          </div>

          <button style={styles.saveButton} onClick={handleSave}>
            Save
          </button>
        </div>
      </div>
    </div>
  )
}

const styles = {
  page: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    fontFamily: 'Arial, sans-serif',
  },
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
  },
  content: {
    padding: '30px',
  },
  card: {
    backgroundColor: '#fff',
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '25px',
    maxWidth: '500px',
  },
  title: {
    marginTop: 0,
    marginBottom: '20px',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    marginBottom: '15px',
  },
  label: {
    fontSize: '13px',
    color: '#555',
    marginBottom: '5px',
  },
  input: {
    padding: '8px',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '14px',
  },
  textarea: {
    padding: '8px',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '14px',
    fontFamily: 'Arial, sans-serif',
    resize: 'vertical',
  },
  saveButton: {
    marginTop: '10px',
    padding: '8px 20px',
    backgroundColor: '#2563eb',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
}

export default Warehouse