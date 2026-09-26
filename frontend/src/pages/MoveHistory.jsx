import { useState } from 'react'
import Navbar from '../components/Navbar'

function MoveHistory() {
  const [search, setSearch] = useState('')

  const moves = [
    { reference: 'WH/IN/0001', date: '12/1/2001', contact: 'Acura Interior', from: 'vendor', to: 'WH/Stock1', quantity: 6, status: 'Ready' },
    { reference: 'WH/OUT/0002', date: '12/1/2001', contact: 'Acura Interior', from: 'WH/Stock1', to: 'vendor', quantity: 4, status: 'Ready' },
    { reference: 'WH/OUT/0002', date: '12/1/2001', contact: 'Acura Interior', from: 'WH/Stock2', to: 'vendor', quantity: 2, status: 'Ready' },
  ]

  const filteredMoves = moves.filter(
    (m) => m.reference.toLowerCase().includes(search.toLowerCase()) || m.contact.toLowerCase().includes(search.toLowerCase())
  )

  const getRowStyle = (m) => {
    if (m.status === 'Done' && m.reference.includes('/IN/')) return styles.rowIn
    if (m.status === 'Done' && m.reference.includes('/OUT/')) return styles.rowOut
    return {}
  }

  const getStatusBadgeStyle = (status) => {
    if (status === 'Done') return styles.statusDone
    if (status === 'Waiting') return styles.statusWaiting
    if (status === 'Late') return styles.statusLate
    return styles.statusReady
  }

  return (
    <div style={styles.page}>
      <Navbar />
      <div style={styles.content}>
        <div style={styles.headerRow}>
          <button style={styles.newButton}>New</button>
          <h2 style={styles.title}>Move History</h2>
          <div style={styles.searchArea}>
            <input type="text" placeholder="Search by reference or contact" value={search} onChange={(e) => setSearch(e.target.value)} style={styles.searchInput} />
            <button style={styles.iconButton} title="List View">☰</button>
            <button style={styles.iconButton} title="Kanban View">▦</button>
          </div>
        </div>

        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Reference</th><th style={styles.th}>Date</th><th style={styles.th}>Contact</th>
              <th style={styles.th}>From</th><th style={styles.th}>To</th><th style={styles.th}>Quantity</th><th style={styles.th}>Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredMoves.map((m, idx) => (
              <tr key={idx} style={getRowStyle(m)}>
                <td style={styles.td}>{m.reference}</td>
                <td style={styles.td}>{m.date}</td>
                <td style={styles.td}>{m.contact}</td>
                <td style={styles.td}>{m.from}</td>
                <td style={styles.td}>{m.to}</td>
                <td style={styles.td}>{m.quantity}</td>
                <td style={styles.td}><span style={{ ...styles.statusBadge, ...getStatusBadgeStyle(m.status) }}>{m.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>

        <div style={styles.legend}>
          <p style={styles.legendItem}><strong>Late:</strong> schedule date &lt; today's date</p>
          <p style={styles.legendItem}><strong>Operations:</strong> schedule date &gt; today's date</p>
          <p style={styles.legendItem}><strong>Waiting:</strong> waiting for the stocks</p>
          <p style={styles.legendItem}>
            <span style={{ color: '#16a34a' }}>■</span> In moves shown in green &nbsp;
            <span style={{ color: '#dc2626' }}>■</span> Out moves shown in red
          </p>
        </div>
      </div>
    </div>
  )
}

const styles = {
  page: { minHeight: '100vh', backgroundColor: '#f5f5f5', fontFamily: 'Arial, sans-serif' },
  content: { padding: '30px' },
  headerRow: { display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '20px' },
  newButton: { padding: '8px 16px', backgroundColor: '#2563eb', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px' },
  title: { margin: 0 },
  searchArea: { marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' },
  searchInput: { padding: '6px 10px', borderRadius: '4px', border: '1px solid #ccc', fontSize: '13px', width: '220px' },
  iconButton: { padding: '6px 10px', border: '1px solid #ccc', borderRadius: '4px', backgroundColor: '#fff', cursor: 'pointer', fontSize: '14px' },
  table: { width: '100%', borderCollapse: 'collapse', backgroundColor: '#fff', border: '1px solid #ddd' },
  th: { textAlign: 'left', padding: '10px', borderBottom: '2px solid #ddd', fontSize: '14px', backgroundColor: '#fafafa' },
  td: { padding: '10px', borderBottom: '1px solid #eee', fontSize: '14px' },
  rowIn: { backgroundColor: '#f0fdf4' },
  rowOut: { backgroundColor: '#fef2f2' },
  statusBadge: { padding: '3px 10px', borderRadius: '12px', fontSize: '12px' },
  statusReady: { backgroundColor: '#dbeafe', color: '#2563eb' },
  statusDone: { backgroundColor: '#dcfce7', color: '#16a34a' },
  statusWaiting: { backgroundColor: '#fef9c3', color: '#ca8a04' },
  statusLate: { backgroundColor: '#fee2e2', color: '#dc2626' },
  legend: { marginTop: '20px', padding: '15px', backgroundColor: '#fff', border: '1px solid #ddd', borderRadius: '6px' },
  legendItem: { fontSize: '13px', color: '#555', margin: '4px 0' },
}

export default MoveHistory