import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'

function Delivery() {
  const [search, setSearch] = useState('')
  const navigate = useNavigate()

  const deliveries = [
    { id: 1, reference: 'WH/OUT/0001', from: 'WH/Stock1', to: 'vendor', contact: 'Acura Interior', scheduleDate: '12/1/2001', status: 'Ready' },
    { id: 2, reference: 'WH/OUT/0002', from: 'WH/Stock1', to: 'vendor', contact: 'Acura Interior', scheduleDate: '12/1/2001', status: 'Ready' },
  ]

  const filteredDeliveries = deliveries.filter(
    (d) => d.reference.toLowerCase().includes(search.toLowerCase()) || d.contact.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div style={styles.page}>
      <Navbar />
      <div style={styles.content}>
        <div style={styles.headerRow}>
          <button style={styles.newButton} onClick={() => navigate('/delivery/new')}>New</button>
          <h2 style={styles.title}>Delivery</h2>
          <div style={styles.searchArea}>
            <input type="text" placeholder="Search by reference or contact" value={search} onChange={(e) => setSearch(e.target.value)} style={styles.searchInput} />
            <button style={styles.iconButton} title="List View">☰</button>
            <button style={styles.iconButton} title="Kanban View">▦</button>
          </div>
        </div>

        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Reference</th>
              <th style={styles.th}>From</th>
              <th style={styles.th}>To</th>
              <th style={styles.th}>Contact</th>
              <th style={styles.th}>Schedule Date</th>
              <th style={styles.th}>Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredDeliveries.map((d) => (
              <tr key={d.id} style={styles.rowHover} onClick={() => navigate(`/delivery/${d.id}`)}>
                <td style={styles.td}>{d.reference}</td>
                <td style={styles.td}>{d.from}</td>
                <td style={styles.td}>{d.to}</td>
                <td style={styles.td}>{d.contact}</td>
                <td style={styles.td}>{d.scheduleDate}</td>
                <td style={styles.td}><span style={styles.statusBadge}>{d.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
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
  rowHover: { cursor: 'pointer' },
  statusBadge: { backgroundColor: '#dcfce7', color: '#16a34a', padding: '3px 10px', borderRadius: '12px', fontSize: '12px' },
}

export default Delivery