import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { api } from '../api'

function DeliveryDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [delivery, setDelivery] = useState(null)
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
      .get(`/api/operations/deliveries/${id}`)
      .then((data) => {
        setDelivery(data)
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
      if (delivery.status === 'Draft') {
        await api.post(`/api/operations/deliveries/${id}/ready`)
      } else if (delivery.status === 'Ready') {
        await api.post(`/api/operations/deliveries/${id}/validate`)
      }
      const updated = await api.get(`/api/operations/deliveries/${id}`)
      setDelivery(updated)
    } catch (err) {
      // Backend should reject validation if stock is insufficient —
      // surface that message here instead of a generic one
      setError(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleCancel = async () => {
    setActionLoading(true)
    setError('')
    try {
      await api.post(`/api/operations/deliveries/${id}/cancel`)
      const updated = await api.get(`/api/operations/deliveries/${id}`)
      setDelivery(updated)
    } catch (err) {
      setError(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handlePrint = async () => {
    try {
      const blob = await api.getBlob(`/api/operations/deliveries/${id}/slip`)
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
          <p style={styles.loading}>Loading delivery...</p>
        </div>
      </div>
    )
  }

  if (error && !delivery) {
    return (
      <div style={styles.page}>
        <Navbar />
        <div style={styles.content}>
          <p style={styles.error}>Failed to load delivery: {error}</p>
          <button style={styles.secondaryButton} onClick={() => navigate('/delivery')}>
            Back to Delivery
          </button>
        </div>
      </div>
    )
  }

  if (!delivery) {
    return (
      <div style={styles.page}>
        <Navbar />
        <div style={styles.content}>
          <p style={styles.error}>No delivery found for this ID.</p>
          <button style={styles.secondaryButton} onClick={() => navigate('/delivery')}>
            Back to Delivery
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.page}>
      <Navbar />
      <div style={styles.content}>
        {error && <p style={styles.alertBox}>⚠ {error}</p>}

        <div style={styles.actionBar}>
          <div>
            <button
              style={{ ...styles.validateButton, ...(delivery.status === 'Done' || actionLoading ? styles.disabledButton : {}) }}
              onClick={handleValidate}
              disabled={delivery.status === 'Done' || actionLoading}
            >
              Validate
            </button>
            <button style={styles.secondaryButton} onClick={handlePrint}>Print</button>
            <button
              style={styles.secondaryButton}
              onClick={handleCancel}
              disabled={actionLoading || delivery.status === 'Done' || delivery.status === 'Cancelled'}
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
                    ...(step === delivery.status ? styles.statusStepActive : {}),
                  }}
                >
                  {step}
                </span>
                {idx < statusSteps.length - 1 && <span style={styles.arrow}>›</span>}
              </span>
            ))}
          </div>
        </div>

        <h2 style={styles.title}>{delivery.delivery_id}</h2>

        <div style={styles.fieldRow}>
          <div style={styles.field}>
            <label style={styles.label}>Customer</label>
            <input style={styles.input} value={delivery.customer_name || ''} readOnly />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Schedule Date</label>
            <input style={styles.input} value={delivery.delivery_date || ''} readOnly />
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
              <td style={styles.td}>{delivery.product_id}</td>
              <td style={styles.td}>{delivery.quantity_delivered}</td>
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
  alertBox: {
    backgroundColor: '#fee2e2',
    color: '#b91c1c',
    padding: '10px 14px',
    borderRadius: '6px',
    fontSize: '13px',
    marginBottom: '15px',
    border: '1px solid #fca5a5',
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

export default DeliveryDetail