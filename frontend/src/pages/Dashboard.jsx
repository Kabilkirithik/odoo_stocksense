import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'

function Dashboard() {
  const navigate = useNavigate()

  return (
    <div style={styles.page}>
      <Navbar />

      <div style={styles.content}>
        <h2 style={styles.title}>Dashboard</h2>

        <div style={styles.cardRow}>
          <div style={styles.card} onClick={() => navigate('/receipts')}>
            <div style={styles.cardHeader}>
              <span style={styles.cardTitle}>Receipt</span>
              <span style={styles.badge}>1 Late</span>
            </div>
            <div style={styles.bigNumber}>4</div>
            <div style={styles.subText}>to receive</div>
            <div style={styles.footerText}>6 operations</div>
          </div>

          <div style={styles.card} onClick={() => navigate('/delivery')}>
            <div style={styles.cardHeader}>
              <span style={styles.cardTitle}>Delivery</span>
              <span style={styles.badge}>1 Late</span>
            </div>
            <div style={styles.bigNumber}>4</div>
            <div style={styles.subText}>to deliver</div>
            <div style={styles.footerRow}>
              <span style={styles.waitingBadge}>2 waiting</span>
              <span style={styles.footerText}>6 operations</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

const styles = {
  page: { minHeight: '100vh', backgroundColor: '#f5f5f5', fontFamily: 'Arial, sans-serif' },
  content: { padding: '30px' },
  title: { marginBottom: '20px' },
  cardRow: { display: 'flex', gap: '20px' },
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
  waitingBadge: { fontSize: '12px', color: '#d97706' },
  bigNumber: { fontSize: '32px', fontWeight: 'bold', color: '#2563eb' },
  subText: { fontSize: '13px', color: '#555', marginBottom: '10px' },
  footerText: { fontSize: '12px', color: '#888' },
  footerRow: { display: 'flex', justifyContent: 'space-between' },
}

export default Dashboard