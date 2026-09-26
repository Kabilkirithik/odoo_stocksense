import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import { api } from '../api'

function MoveHistory() {
  const [search, setSearch] = useState('')
  const [movementType, setMovementType] = useState('')
  const [moves, setMoves] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchMoves()
  }, [])

  const fetchMoves = () => {
    setLoading(true)
    const params = new URLSearchParams()
    if (search) params.set('reference_id', search)
    if (movementType) params.set('movement_type', movementType)
    api
      .get(`/api/moves?${params.toString()}`)
      .then((data) => {
        setMoves(data.items || data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }

  const handleFilterSubmit = (e) => {
    e.preventDefault()
    fetchMoves()
  }

  const getRowStyle = (m) => {
    if (m.movement_type === 'Receipt') return styles.rowIn
    if (m.movement_type === 'Delivery') return styles.rowOut
    return {}
  }

  return (
    <div style={styles.page}>
      <Navbar />
      <div style={styles.content}>
        <div style={styles.headerRow}>
          <h2 style={styles.title}>Move History</h2>

          <form style={styles.searchArea} onSubmit={handleFilterSubmit}>
            <input
              type="text"
              placeholder="Search by reference"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={styles.searchInput}
            />
            <select value={movementType} onChange={(e) => setMovementType(e.target.value)} style={styles.select}>
              <option value="">All types</option>
              <option value="Receipt">Receipt</option>
              <option value="Delivery">Delivery</option>
              <option value="Transfer">Transfer</option>
              <option value="Adjustment">Adjustment</option>
            </select>
            <button type="submit" style={styles.iconButton}>Filter</button>
          </form>
        </div>

        {error && <p style={styles.error}>Failed to load move history: {error}</p>}
        {loading && <p style={styles.loading}>Loading...</p>}

        {!loading && !error && (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Move ID</th>
                <th style={styles.th}>Type</th>
                <th style={styles.th}>Reference</th>
                <th style={styles.th}>Product</th>
                <th style={styles.th}>From</th>
                <th style={styles.th}>To</th>
                <th style={styles.th}>Quantity</th>
                <th style={styles.th}>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {moves.map((m) => (
                <tr key={m.move_id} style={getRowStyle(m)}>
                  <td style={styles.td}>{m.move_id}</td>
                  <td style={styles.td}>{m.movement_type}</td>
                  <td style={styles.td}>{m.reference_id}</td>
                  <td style={styles.td}>{m.product_id}</td>
                  <td style={styles.td}>{m.from_location}</td>
                  <td style={styles.td}>{m.to_location}</td>
                  <td style={styles.td}>{m.quantity}</td>
                  <td style={styles.td}>{m.timestamp}</td>
                </tr>
              ))}
              {moves.length === 0 && (
                <tr><td style={styles.td} colSpan={8}>No movements found.</td></tr>
              )}
            </tbody>
          </table>
        )}

        <div style={styles.legend}>
          <p style={styles.legendItem}>
            <span style={{ color: '#16a34a' }}>■</span> Receipts shown in green &nbsp;
            <span style={{ color: '#dc2626' }}>■</span> Deliveries shown in red
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
  title: { margin: 0 },
  searchArea: { marginLeft: 'auto', display: 'flex', gap: '8px' },
  searchInput: { padding: '6px 10px', borderRadius: '4px', border: '1px solid #ccc', fontSize: '13px', width: '200px' },
  select: { padding: '6px 10px', borderRadius: '4px', border: '1px solid #ccc', fontSize: '13px' },
  iconButton: { padding: '6px 12px', border: '1px solid #ccc', borderRadius: '4px', backgroundColor: '#fff', cursor: 'pointer', fontSize: '13px' },
  loading: { color: '#888', fontSize: '14px' },
  error: { color: '#dc2626', fontSize: '14px', marginBottom: '15px' },
  table: { width: '100%', borderCollapse: 'collapse', backgroundColor: '#fff', border: '1px solid #ddd' },
  th: { textAlign: 'left', padding: '10px', borderBottom: '2px solid #ddd', fontSize: '14px', backgroundColor: '#fafafa' },
  td: { padding: '10px', borderBottom: '1px solid #eee', fontSize: '14px' },
  rowIn: { backgroundColor: '#f0fdf4' },
  rowOut: { backgroundColor: '#fef2f2' },
  legend: { marginTop: '20px', padding: '15px', backgroundColor: '#fff', border: '1px solid #ddd', borderRadius: '6px' },
  legendItem: { fontSize: '13px', color: '#555', margin: '4px 0' },
}

export default MoveHistory