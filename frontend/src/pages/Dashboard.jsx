// src/pages/Dashboard.jsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { api } from '../api'

function Dashboard() {
  const navigate = useNavigate()
  const [kpis, setKpis] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get('/api/dashboard/kpis')
      .then(setKpis)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <div style={styles.page}>
      <Navbar />

      <div style={styles.content}>
        <h2 style={styles.title}>Dashboard</h2>

        {error && <p style={styles.error}>Failed to load dashboard: {error}</p>}

        {!kpis && !error && <p style={styles.loading}>Loading...</p>}

        {kpis && (
          <div style={styles.cardRow}>
            <div style={styles.card} onClick={() => navigate('/receipts')}>
              <div style={styles.cardHeader}>
                <span style={styles.cardTitle}>Receipt</span>
              </div>
              <div style={styles.bigNumber}>{kpis.pending_receipts}</div>
              <div style={styles.subText}>to receive</div>
            </div>

            <div style={styles.card} onClick={() => navigate('/delivery')}>
              <div style={styles.cardHeader}>
                <span style={styles.cardTitle}>Delivery</span>
              </div>
              <div style={styles.bigNumber}>{kpis.pending_deliveries}</div>
              <div style={styles.subText}>to deliver</div>
            </div>

            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <span style={styles.cardTitle}>Total Products</span>
              </div>
              <div style={styles.bigNumber}>{kpis.total_products}</div>
            </div>

            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <span style={styles.cardTitle}>Low Stock Items</span>
                <span style={styles.badge}>Alert</span>
              </div>
              <div style={styles.bigNumber}>{kpis.low_stock_items}</div>
            </div>

            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <span style={styles.cardTitle}>Internal Transfers</span>
              </div>
              <div style={styles.bigNumber}>{kpis.internal_transfers_scheduled}</div>
              <div style={styles.subText}>scheduled</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

const styles = {
  page: { minHeight: '100vh', backgroundColor: '#f5f5f5', fontFamily: 'Arial, sans-serif' },
  content: { padding: '30px' },
  title: { marginBottom: '20px' },
  loading: { color: '#888', fontSize: '14px' },
  error: { color: '#dc2626', fontSize: '14px', marginBottom: '15px' },
  cardRow: { display: 'flex', gap: '20px', flexWrap: 'wrap' },
  card: {
    backgroundColor: '#fff',
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '20px',
    width: '220px',
    cursor: 'pointer',
  },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' },
  cardTitle: { fontSize: '16px', fontWeight: 'bold' },
  badge: { fontSize: '12px', color: '#dc2626' },
  bigNumber: { fontSize: '32px', fontWeight: 'bold', color: '#2563eb' },
  subText: { fontSize: '13px', color: '#555', marginBottom: '10px' },
}

export default Dashboard