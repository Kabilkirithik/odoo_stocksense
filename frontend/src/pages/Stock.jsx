import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import { api } from '../api'

function Stock() {
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [savingId, setSavingId] = useState(null)

  useEffect(() => {
    api.get('/api/products/categories').then(setCategories).catch(() => {})
    fetchProducts()
  }, [])

  const fetchProducts = () => {
    setLoading(true)
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (category) params.set('category', category)
    api
      .get(`/api/products?${params.toString()}`)
      .then((data) => {
        setProducts(data.items || data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }

  const handleFilterSubmit = (e) => {
    e.preventDefault()
    fetchProducts()
  }

  const handleFieldChange = (sku, field, value) => {
    setProducts((prev) =>
      prev.map((p) =>
        p.product_id === sku
          ? { ...p, [field]: field === 'product_name' ? value : Number(value) }
          : p
      )
    )
  }

  const handleSave = async (product) => {
    setSavingId(product.product_id)
    setError('')
    try {
      await api.put(`/api/products/${product.product_id}`, {
        product_name: product.product_name,
        stock_quantity: product.stock_quantity,
        unit_price: product.unit_price,
      })
    } catch (err) {
      setError(`Failed to save ${product.product_id}: ${err.message}`)
    } finally {
      setSavingId(null)
    }
  }

  const handleDelete = async (sku) => {
    if (!window.confirm(`Delete product ${sku}?`)) return
    try {
      await api.delete(`/api/products/${sku}`)
      setProducts((prev) => prev.filter((p) => p.product_id !== sku))
    } catch (err) {
      setError(`Failed to delete ${sku}: ${err.message}`)
    }
  }

  return (
    <div style={styles.page}>
      <Navbar />
      <div style={styles.content}>
        <div style={styles.headerRow}>
          <h2 style={styles.title}>Stock</h2>

          <form style={styles.filterArea} onSubmit={handleFilterSubmit}>
            <input
              type="text"
              placeholder="Search by name or SKU"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={styles.searchInput}
            />
            <select value={category} onChange={(e) => setCategory(e.target.value)} style={styles.select}>
              <option value="">All categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            <button type="submit" style={styles.iconButton}>Filter</button>
          </form>
        </div>

        {error && <p style={styles.error}>{error}</p>}
        {loading && <p style={styles.loading}>Loading...</p>}

        {!loading && (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>SKU</th>
                <th style={styles.th}>Product</th>
                <th style={styles.th}>Category</th>
                <th style={styles.th}>Per Unit Cost</th>
                <th style={styles.th}>On Hand</th>
                <th style={styles.th}>Warehouse</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.product_id}>
                  <td style={styles.td}>{p.product_id}</td>
                  <td style={styles.td}>
                    <input
                      style={styles.input}
                      value={p.product_name}
                      onChange={(e) => handleFieldChange(p.product_id, 'product_name', e.target.value)}
                    />
                  </td>
                  <td style={styles.td}>{p.category}</td>
                  <td style={styles.td}>
                    <input
                      style={styles.input}
                      type="number"
                      value={p.unit_price}
                      onChange={(e) => handleFieldChange(p.product_id, 'unit_price', e.target.value)}
                    />
                  </td>
                  <td style={styles.td}>
                    <input
                      style={styles.input}
                      type="number"
                      value={p.stock_quantity}
                      onChange={(e) => handleFieldChange(p.product_id, 'stock_quantity', e.target.value)}
                    />
                  </td>
                  <td style={styles.td}>{p.warehouse_name}</td>
                  <td style={styles.td}>
                    <button
                      style={styles.saveButton}
                      onClick={() => handleSave(p)}
                      disabled={savingId === p.product_id}
                    >
                      {savingId === p.product_id ? 'Saving...' : 'Save'}
                    </button>
                    <button style={styles.deleteButton} onClick={() => handleDelete(p.product_id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {products.length === 0 && (
                <tr><td style={styles.td} colSpan={7}>No products found.</td></tr>
              )}
            </tbody>
          </table>
        )}

        <p style={styles.note}>User must be able to update the stock from here.</p>
      </div>
    </div>
  )
}

const styles = {
  page: { minHeight: '100vh', backgroundColor: '#f5f5f5', fontFamily: 'Arial, sans-serif' },
  content: { padding: '30px' },
  headerRow: { display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '20px' },
  title: { margin: 0 },
  filterArea: { marginLeft: 'auto', display: 'flex', gap: '8px' },
  searchInput: { padding: '6px 10px', borderRadius: '4px', border: '1px solid #ccc', fontSize: '13px', width: '200px' },
  select: { padding: '6px 10px', borderRadius: '4px', border: '1px solid #ccc', fontSize: '13px' },
  iconButton: { padding: '6px 12px', border: '1px solid #ccc', borderRadius: '4px', backgroundColor: '#fff', cursor: 'pointer', fontSize: '13px' },
  loading: { color: '#888', fontSize: '14px' },
  error: { color: '#dc2626', fontSize: '14px', marginBottom: '15px' },
  table: { width: '100%', borderCollapse: 'collapse', backgroundColor: '#fff', border: '1px solid #ddd' },
  th: { textAlign: 'left', padding: '10px', borderBottom: '2px solid #ddd', fontSize: '14px', backgroundColor: '#fafafa' },
  td: { padding: '8px 10px', borderBottom: '1px solid #eee', fontSize: '14px' },
  input: { border: '1px solid #ddd', background: '#fff', width: '90px', fontSize: '14px', padding: '4px', borderRadius: '4px' },
  saveButton: { padding: '4px 10px', backgroundColor: '#2563eb', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px', marginRight: '6px' },
  deleteButton: { padding: '4px 10px', backgroundColor: '#fff', color: '#dc2626', border: '1px solid #dc2626', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' },
  note: { marginTop: '20px', fontSize: '13px', color: '#888' },
}

export default Stock