import { useState } from 'react'
import Navbar from '../components/Navbar'

function Stock() {
  const [products, setProducts] = useState([
    { id: 1, name: 'Desk', cost: 3000, onHand: 50, freeToUse: 45 },
    { id: 2, name: 'Table', cost: 3000, onHand: 50, freeToUse: 50 },
  ])

  const handleChange = (id, field, value) => {
    setProducts((prev) =>
      prev.map((p) => (p.id === id ? { ...p, [field]: field === 'name' ? value : Number(value) } : p))
    )
  }

  return (
    <div style={styles.page}>
      <Navbar />
      <div style={styles.content}>
        <h2 style={styles.title}>Stock</h2>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Product</th>
              <th style={styles.th}>Per Unit Cost</th>
              <th style={styles.th}>On Hand</th>
              <th style={styles.th}>Free to Use</th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id}>
                <td style={styles.td}>
                  <input style={styles.input} value={p.name} onChange={(e) => handleChange(p.id, 'name', e.target.value)} />
                </td>
                <td style={styles.td}>
                  <input style={styles.input} type="number" value={p.cost} onChange={(e) => handleChange(p.id, 'cost', e.target.value)} /> Rs
                </td>
                <td style={styles.td}>
                  <input style={styles.input} type="number" value={p.onHand} onChange={(e) => handleChange(p.id, 'onHand', e.target.value)} />
                </td>
                <td style={styles.td}>
                  <input style={styles.input} type="number" value={p.freeToUse} onChange={(e) => handleChange(p.id, 'freeToUse', e.target.value)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p style={styles.note}>User must be able to update the stock from here.</p>
      </div>
    </div>
  )
}

const styles = {
  page: { minHeight: '100vh', backgroundColor: '#f5f5f5', fontFamily: 'Arial, sans-serif' },
  content: { padding: '30px' },
  title: { marginBottom: '20px' },
  table: { width: '100%', maxWidth: '700px', borderCollapse: 'collapse', backgroundColor: '#fff', border: '1px solid #ddd' },
  th: { textAlign: 'left', padding: '10px', borderBottom: '2px solid #ddd', fontSize: '14px', backgroundColor: '#fafafa' },
  td: { padding: '8px 10px', borderBottom: '1px solid #eee', fontSize: '14px' },
  input: { border: 'none', background: 'transparent', width: '80px', fontSize: '14px', padding: '4px' },
  note: { marginTop: '20px', fontSize: '13px', color: '#888' },
}

export default Stock