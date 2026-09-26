import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import { api } from '../api'

function Warehouse() {
  const [warehouses, setWarehouses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get('/api/warehouses')
      .then((data) => {
        setWarehouses(data.items || data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  return (
    <div style={styles.page}>
      <Navbar />
      <div style={styles.content}>
        <h2 style={styles.title}>Warehouse</h2>

        {error && <p style={styles.error}>Failed to load warehouses: {error}</p>}
        {loading && <p style={styles.loading}>Loading...</p>}

        {!loading && !error && (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Warehouse ID</th>
                <th style={styles.th}>Name</th>
                <th style={styles.th}>City</th>
                <th style={styles.th}>Capacity</th>
              </tr>
            </thead>
            <tbody>
              {warehouses.map((w) => (
                <tr key={w.warehouse_id}>
                  <td style={styles.td}>{w.warehouse_id}</td>
                  <td style={styles.td}>{w.warehouse_name}</td>
                  <td style={styles.td}>{w.city}</td>
                  <td style={styles.td}>{w.capacity}</td>
                </tr>
              ))}
              {warehouses.length === 0 && (
                <tr><td style={styles.td} colSpan={4}>No warehouses found.</td></tr>
              )}
            </tbody>
          </table>
        )}

        <p style={styles.note}>
          Note: warehouse creation isn't part of the current API — this is a read-only list.
        </p>
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
  table: { width: '100%', maxWidth: '700px', borderCollapse: 'collapse', backgroundColor: '#fff', border: '1px solid #ddd' },
  th: { textAlign: 'left', padding: '10px', borderBottom: '2px solid #ddd', fontSize: '14px', backgroundColor: '#fafafa' },
  td: { padding: '10px', borderBottom: '1px solid #eee', fontSize: '14px' },
  note: { marginTop: '15px', fontSize: '13px', color: '#888' },
}

export default Warehouse