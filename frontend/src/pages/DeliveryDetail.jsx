import { useState } from 'react'
import Navbar from '../components/Navbar'

function DeliveryDetail() {
  const [status, setStatus] = useState('Draft')
  const [products, setProducts] = useState([{ id: 1, code: 'DESK001', name: 'Desk', quantity: 6, availableStock: 4 }])
  const loggedInUser = 'Admin'

  const handleQuantityChange = (id, value) => {
    setProducts((prev) => prev.map((p) => (p.id === id ? { ...p, quantity: Number(value) } : p)))
  }

  const addProduct = () => {
    setProducts((prev) => [...prev, { id: prev.length + 1, code: '', name: '', quantity: 0, availableStock: 0 }])
  }

  const statusSteps = ['Draft', 'Waiting', 'Ready', 'Done']
  const hasOutOfStock = products.some((p) => p.quantity > p.availableStock)

  const handleValidate = () => {
    if (hasOutOfStock) return
    const currentIndex = statusSteps.indexOf(status)
    if (currentIndex < statusSteps.length - 1) setStatus(statusSteps[currentIndex + 1])
  }

  return (
    <div style={styles.page}>
      <Navbar />
      <div style={styles.content}>
        <div style={styles.actionBar}>
          <div>
            <button
              style={{ ...styles.validateButton, ...(hasOutOfStock || status === 'Done' ? styles.disabledButton : {}) }}
              onClick={handleValidate}
              disabled={hasOutOfStock || status === 'Done'}
            >
              Validate
            </button>
            <button style={styles.secondaryButton}>Print</button>
            <button style={styles.secondaryButton}>Cancel</button>
          </div>
          <div style={styles.statusBar}>
            {statusSteps.map((step, idx) => (
              <span key={step} style={styles.statusStepWrapper}>
                <span style={{ ...styles.statusStep, ...(step === status ? styles.statusStepActive : {}) }}>{step}</span>
                {idx < statusSteps.length - 1 && <span style={styles.arrow}>›</span>}
              </span>
            ))}
          </div>
        </div>

        <h2 style={styles.title}>WH/OUT/0001</h2>

        {hasOutOfStock && (
          <div style={styles.alertBox}>⚠ One or more products are out of stock. Please adjust quantity or wait for restock.</div>
        )}

        <div style={styles.fieldRow}>
          <div style={styles.field}>
            <label style={styles.label}>Delivery Address</label>
            <input style={styles.input} placeholder="Customer / vendor address" />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Schedule Date</label>
            <input style={styles.input} type="date" />
          </div>
        </div>

        <div style={styles.fieldRow}>
          <div style={styles.field}>
            <label style={styles.label}>Responsible</label>
            <input style={styles.input} value={loggedInUser} readOnly />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Operation Type</label>
            <input style={styles.input} placeholder="Delivery" />
          </div>
        </div>

        <h3 style={styles.subTitle}>Products</h3>
        <table style={styles.table}>
          <thead>
            <tr><th style={styles.th}>Product</th><th style={styles.th}>Quantity</th></tr>
          </thead>
          <tbody>
            {products.map((p) => {
              const outOfStock = p.quantity > p.availableStock
              return (
                <tr key={p.id} style={outOfStock ? styles.rowAlert : {}}>
                  <td style={styles.td}>
                    [{p.code}] {p.name}
                    {outOfStock && <span style={styles.outOfStockTag}> Not enough stock ({p.availableStock} available)</span>}
                  </td>
                  <td style={styles.td}>
                    <input
                      style={{ ...styles.qtyInput, ...(outOfStock ? styles.qtyInputAlert : {}) }}
                      type="number"
                      value={p.quantity}
                      onChange={(e) => handleQuantityChange(p.id, e.target.value)}
                    />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>

        <button style={styles.addProductButton} onClick={addProduct}>+ New Product</button>
      </div>
    </div>
  )
}

const styles = {
  page: { minHeight: '100vh', backgroundColor: '#f5f5f5', fontFamily: 'Arial, sans-serif' },
  content: { padding: '30px', maxWidth: '800px' },
  actionBar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' },
  validateButton: { padding: '8px 16px', backgroundColor: '#2563eb', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px', marginRight: '8px' },
  disabledButton: { backgroundColor: '#ccc', cursor: 'not-allowed' },
  secondaryButton: { padding: '8px 16px', backgroundColor: '#fff', color: '#333', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer', fontSize: '14px', marginRight: '8px' },
  statusBar: { display: 'flex', alignItems: 'center', gap: '6px' },
  statusStepWrapper: { display: 'flex', alignItems: 'center', gap: '6px' },
  statusStep: { fontSize: '13px', color: '#999', padding: '4px 10px', border: '1px solid #ddd', borderRadius: '12px' },
  statusStepActive: { color: '#fff', backgroundColor: '#2563eb', borderColor: '#2563eb', fontWeight: 'bold' },
  arrow: { color: '#999' },
  title: { marginBottom: '10px' },
  alertBox: { backgroundColor: '#fee2e2', color: '#b91c1c', padding: '10px 14px', borderRadius: '6px', fontSize: '13px', marginBottom: '15px', border: '1px solid #fca5a5' },
  fieldRow: { display: 'flex', gap: '30px', marginBottom: '15px' },
  field: { display: 'flex', flexDirection: 'column', flex: 1 },
  label: { fontSize: '13px', color: '#555', marginBottom: '4px' },
  input: { padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' },
  subTitle: { marginTop: '25px', marginBottom: '10px' },
  table: { width: '100%', borderCollapse: 'collapse', backgroundColor: '#fff', border: '1px solid #ddd' },
  th: { textAlign: 'left', padding: '10px', borderBottom: '2px solid #ddd', fontSize: '14px', backgroundColor: '#fafafa' },
  td: { padding: '10px', borderBottom: '1px solid #eee', fontSize: '14px' },
  rowAlert: { backgroundColor: '#fef2f2' },
  outOfStockTag: { color: '#dc2626', fontSize: '12px', marginLeft: '8px' },
  qtyInput: { width: '60px', padding: '4px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' },
  qtyInputAlert: { border: '1px solid #dc2626', backgroundColor: '#fff5f5' },
  addProductButton: { marginTop: '10px', padding: '6px 12px', backgroundColor: '#fff', border: '1px dashed #999', borderRadius: '4px', cursor: 'pointer', fontSize: '13px', color: '#555' },
}

export default DeliveryDetail