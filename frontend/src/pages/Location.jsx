import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import { api } from '../api'

function Location() {
  const [locations, setLocations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get('/api/warehouses/locations')
      .then((data) => {
        setLocations(data.locations || [])
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
        <div style={styles.card}>
          <h2 style={styles.title}>Locations</h2>

          {error && <p style={styles.error}>Failed to load locations: {error}</p>}
          {loading && <p style={styles.loading}>Loading...</p>}

          {!loading && !error && (
            <ul style={styles.list}>
              {locations.map((loc) => (
                <li key={loc} style={styles.listItem}>{loc}</li>
              ))}
              {locations.length === 0 && <li style={styles.listItem}>No locations found.</li>}
            </ul>
          )}

          <p style={styles.note}>
            This holds the multiple locations of a warehouse, rooms, racks, etc.
            Note: location creation isn't part of the current API — this is a read-only list.
          </p>
        </div>
      </div>
    </div>
  )
}

const styles = {
  page: { minHeight: '100vh', backgroundColor: '#f5f5f5', fontFamily: 'Arial, sans-serif' },
  content: { padding: '30px' },
  card: { backgroundColor: '#fff', border: '1px solid #ddd', borderRadius: '8px', padding: '25px', maxWidth: '500px' },
  title: { marginTop: 0, marginBottom: '20px' },
  loading: { color: '#888', fontSize: '14px' },
  error: { color: '#dc2626', fontSize: '14px', marginBottom: '15px' },
  list: { listStyle: 'none', padding: 0, margin: 0 },
  listItem: { padding: '8px 0', borderBottom: '1px solid #eee', fontSize: '14px' },
  note: { fontSize: '13px', color: '#888', marginTop: '15px' },
}

export default Location