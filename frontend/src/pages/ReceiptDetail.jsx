import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { api } from '../api'

function ReceiptDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [receipt, setReceipt] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionLoading, setActionLoading] = useState(false)

  const loggedInUser = 'Admin' // TODO: replace with real logged-in user later

  const statusSteps = ['Draft', 'Ready', 'Done']

  useEffect(() => {
    if (!id || id === 'new') {
      setLoading(false)
      return
    }
    api
      .get(`/api/operations/receipts/${id}`)
      .then((data) => {
        setReceipt(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [id])

  const handleValidate = async () => {
    setActionLoading(true)
    setError('')
    try {
      if (receipt.status === 'Draft') {
        await api.post(`/api/operations/receipts/${id}/ready`)
      } else if (receipt.status === 'Ready') {
        await api.post(`/api/operations/receipts/${id}/validate`)
      }
      const updated = await api.get(`/api/operations/receipts/${id}`)
      setReceipt(updated)
    } catch (err) {
      setError(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleCancel = async () => {
    setActionLoading(true)
    setError('')
    try {
      await api.post(`/api/operations/receipts/${id}/cancel`)
      const updated = await api.get(`/api/operations/receipts/${id}`)
      setReceipt(updated)
    } catch (err) {
      setError(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handlePrint = async () => {
    try {
      const blob = await api.getBlob(`/api/operations/receipts/${id}/slip`)
      const url = window.URL.createObjectURL(blob)
      window.open(url, '_blank')
    } catch (err) {
      alert('Failed to load print slip: ' + err.message)
    }
  }

  if (loading) {
    return (
      <div style={styles.page}>
        <Navbar />
        <div style={styles.content}>
          <p style={styles.loading}>Loading receipt...</p>
        </div>
      </div>
    )
  }

  if (error && !receipt) {
    return (
      <div style={styles.page}>
        <Navbar />
        <div style={styles.content}>
          <p style={styles.error}>Failed to load receipt: {error}</p>
          <button style={styles.secondaryButton} onClick={() => navigate('/receipts')}>
            Back to Receipts
          </button>
        </div>
      </div>
    )
  }

  if (!receipt) {
    return (
      <div style={styles.page}>
        <Navbar />
        <div style={styles.content}>
          <p style={styles.error}>No receipt found for this ID.</p>
          <button style={styles.secondaryButton} onClick={() => navigate('/receipts')}>
            Back to Receipts
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.page}>
      <Navbar />
      <div style={styles.content}>
        {error && <p style={styles.error}>{error}</p>}

        <div style={styles.actionBar}>
          <div>
            <button
              style={{ ...styles.validateButton, ...(receipt.status === 'Done' || actionLoading ? styles.disabledButton : {}) }}
              onClick={handleValidate}
              disabled={receipt.status === 'Done' || actionLoading}
            >
              Validate
            </button>
            <button style={styles.secondaryButton} onClick={handlePrint}>Print</button>
            <button
              style={styles.secondaryButton}
              onClick={handleCancel}
              disabled={actionLoading || receipt.status === 'Done' || receipt.status === 'Cancelled'}
            >
              Cancel
            </button>
          </div>

          <div style={styles.statusBar}>
            {statusSteps.map((step, idx) => (
              <span key={step} style={styles.statusStepWrapper}>
                <span
                  style={{
                    ...styles.statusStep,
                    ...(step === receipt.status ? styles.statusStepActive : {}),
                  }}
                >
                  {step}
                </span>
                {idx < statusSteps.length - 1 && <span style={styles.arrow}>›</span>}
              </span>
            ))}
          </div>
        </div>

        <h2 style={styles.title}>{receipt.receipt_id}</h2>

        <div style={styles.fieldRow}>
          <div style={styles.field}>
            <label style={styles.label}>Receive From</label>
            <input style={styles.input} value={receipt.supplier_id || ''} readOnly />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Schedule Date</label>
            <input style={styles.input} value={receipt.receipt_date || ''} readOnly />
          </div>
        </div>

        <div style={styles.fieldRow}>
          <div style={styles.field}>
            <label style={styles.label}>Responsible</label>
            <input style={styles.input} value={loggedInUser} readOnly />
          </div>
        </div>

        <h3 style={styles.subTitle}>Products</h3>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Product</th>
              <th style={styles.th}>Quantity</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={styles.td}>{receipt.product_id}</td>
              <td style={styles.td}>{receipt.quantity_received}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

const styles = {
  page: { minHeight: '100vh', backgroundColor: '#f5f5f5', fontFamily: 'Arial, sans-serif' },
  content: { padding: '30px', maxWidth: '800px' },
  loading: { color: '#888', fontSize: '14px' },
  error: {
    color: '#dc2626',
    fontSize: '13px',
    marginBottom: '15px',
    backgroundColor: '#fee2e2',
    padding: '10px',
    borderRadius: '6px',
  },
  actionBar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' },
  validateButton: {
    padding: '8px 16px',
    backgroundColor: '#2563eb',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    marginRight: '8px',
  },
  disabledButton: { backgroundColor: '#ccc', cursor: 'not-allowed' },
  secondaryButton: {
    padding: '8px 16px',
    backgroundColor: '#fff',
    color: '#333',
    border: '1px solid #ccc',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    marginRight: '8px',
  },
  statusBar: { display: 'flex', alignItems: 'center', gap: '6px' },
  statusStepWrapper: { display: 'flex', alignItems: 'center', gap: '6px' },
  statusStep: { fontSize: '13px', color: '#999', padding: '4px 10px', border: '1px solid #ddd', borderRadius: '12px' },
  statusStepActive: { color: '#fff', backgroundColor: '#2563eb', borderColor: '#2563eb', fontWeight: 'bold' },
  arrow: { color: '#999' },
  title: { marginBottom: '20px' },
  fieldRow: { display: 'flex', gap: '30px', marginBottom: '15px' },
  field: { display: 'flex', flexDirection: 'column', flex: 1 },
  label: { fontSize: '13px', color: '#555', marginBottom: '4px' },
  input: { padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px', backgroundColor: '#fff' },
  subTitle: { marginTop: '25px', marginBottom: '10px' },
  table: { width: '100%', borderCollapse: 'collapse', backgroundColor: '#fff', border: '1px solid #ddd' },
  th: { textAlign: 'left', padding: '10px', borderBottom: '2px solid #ddd', fontSize: '14px', backgroundColor: '#fafafa' },
  td: { padding: '10px', borderBottom: '1px solid #eee', fontSize: '14px' },
}

export default ReceiptDetail