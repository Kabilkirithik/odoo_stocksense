import { useState } from 'react'
import Navbar from '../components/Navbar'

function Location() {
  const [location, setLocation] = useState({ name: '', shortCode: '', warehouse: '' })
  const warehouseOptions = ['WH - Main Warehouse']

  const handleChange = (field, value) => {
    setLocation((prev) => ({ ...prev, [field]: value }))
  }

  const handleSave = () => {
    console.log('Location saved:', location)
  }

  return (
    <div style={styles.page}>
      <Navbar />
      <div style={styles.content}>
        <div style={styles.card}>
          <h2 style={styles.title}>Location</h2>

          <div style={styles.field}>
            <label style={styles.label}>Name</label>
            <input style={styles.input} value={location.name} onChange={(e) => handleChange('name', e.target.value)} placeholder="e.g. Rack A, Production Floor" />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Short Code</label>
            <input style={styles.input} value={location.shortCode} onChange={(e) => handleChange('shortCode', e.target.value)} placeholder="e.g. Stock1" />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Warehouse</label>
            <select style={styles.input} value={location.warehouse} onChange={(e) => handleChange('warehouse', e.target.value)}>
              <option value="">Select warehouse</option>
              {warehouseOptions.map((w) => <option key={w} value={w}>{w}</option>)}
            </select>
          </div>

          <p style={styles.note}>This holds the multiple locations of a warehouse, rooms, racks, etc.</p>

          <button style={styles.saveButton} onClick={handleSave}>Save</button>
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
  field: { display: 'flex', flexDirection: 'column', marginBottom: '15px' },
  label: { fontSize: '13px', color: '#555', marginBottom: '5px' },
  input: { padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' },
  note: { fontSize: '13px', color: '#888', marginBottom: '15px' },
  saveButton: { marginTop: '10px', padding: '8px 20px', backgroundColor: '#2563eb', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px' },
}

export default Location