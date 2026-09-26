import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { api } from '../api'

function Receipts() {
  const [search, setSearch] = useState('')
  const [receipts, setReceipts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    fetchReceipts()
  }, [])

  const fetchReceipts = () => {
    setLoading(true)
    const query = search ? `?search=${encodeURIComponent(search)}` : ''
    api
      .get(`/api/operations/receipts${query}`)
      .then((data) => {
        setReceipts(data.items || data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    fetchReceipts()
  }

  return (
    <div style={styles.page}>
      <Navbar />
      <div style={styles.content}>
        <div style={styles.headerRow}>
          <button style={styles.newButton} onClick={() => navigate('/receipts/new')}>New</button>
          <h2 style={styles.title}>Receipts</h2>

          <form style={styles.searchArea} onSubmit={handleSearchSubmit}>
            <input
              type="text"
              placeholder="Search by reference or supplier"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={styles.searchInput}
            />
            <button type="submit" style={styles.iconButton} title="Search">🔍</button>
          </form>
        </div>

        {error && <p style={styles.error}>Failed to load receipts: {error}</p>}
        {loading && <p style={styles.loading}>Loading...</p>}

        {!loading && !error && (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Reference</th>
                <th style={styles.th}>Supplier</th>
                <th style={styles.th}>Product</th>
                <th style={styles.th}>Quantity</th>
                <th style={styles.th}>Date</th>
                <th style={styles.th}>Status</th>
              </tr>
            </thead>
            <tbody>
              {receipts.map((r) => (
                <tr key={r.receipt_id} style={styles.rowHover} onClick={() => navigate(`/receipts/${r.receipt_id}`)}>
                  <td style={styles.td}>{r.receipt_id}</td>
                  <td style={styles.td}>{r.supplier_id}</td>
                  <td style={styles.td}>{r.product_id}</td>
                  <td style={styles.td}>{r.quantity_received}</td>
                  <td style={styles.td}>{r.receipt_date}</td>
                  <td style={styles.td}><span style={styles.statusBadge}>{r.status}</span></td>
                </tr>
              ))}
              {receipts.length === 0 && (
                <tr><td style={styles.td} colSpan={6}>No receipts found.</td></tr>
              )}
            </tbody>
          </table>
        )}
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
  loading: { color: '#888', fontSize: '14px' },
  error: { color: '#dc2626', fontSize: '14px', marginBottom: '15px' },
  table: { width: '100%', borderCollapse: 'collapse', backgroundColor: '#fff', border: '1px solid #ddd' },
  th: { textAlign: 'left', padding: '10px', borderBottom: '2px solid #ddd', fontSize: '14px', backgroundColor: '#fafafa' },
  td: { padding: '10px', borderBottom: '1px solid #eee', fontSize: '14px' },
  rowHover: { cursor: 'pointer' },
  statusBadge: { backgroundColor: '#dcfce7', color: '#16a34a', padding: '3px 10px', borderRadius: '12px', fontSize: '12px' },
}

export default Receipts