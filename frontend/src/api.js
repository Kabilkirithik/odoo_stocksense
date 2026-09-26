// src/api.js
const BASE_URL = 'http://127.0.0.1:8000'

function buildQueryString(params = {}) {
  const searchParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    searchParams.append(key, String(value))
  })

  const queryString = searchParams.toString()
  return queryString ? `?${queryString}` : ''
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}))
    throw new Error(errorBody.detail || `Request failed: ${res.status}`)
  }

  const text = await res.text()
  return text ? JSON.parse(text) : null
}

// For endpoints that return a file (e.g. PDF slips) instead of JSON
async function requestBlob(path) {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`)
  }
  return res.blob()
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
  put: (path, body) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
  delete: (path) => request(path, { method: 'DELETE' }),
  getBlob: (path) => requestBlob(path),

  dashboard: {
    getKpis: () => api.get('/api/dashboard/kpis'),
    getActivity: (limit = 10) => api.get(`/api/dashboard/activity${buildQueryString({ limit })}`),
    getLowStock: (limit = 10) => api.get(`/api/dashboard/low-stock${buildQueryString({ limit })}`),
  },

  products: {
    list: (params = {}) => api.get(`/api/products${buildQueryString(params)}`),
    getBySku: (sku) => api.get(`/api/products/${encodeURIComponent(sku)}`),
    create: (payload) => api.post('/api/products', payload),
    update: (sku, payload) => api.put(`/api/products/${encodeURIComponent(sku)}`, payload),
    remove: (sku) => api.delete(`/api/products/${encodeURIComponent(sku)}`),
    categories: () => api.get('/api/products/categories'),
  },

  warehouses: {
    list: (params = {}) => api.get(`/api/warehouses${buildQueryString(params)}`),
    locations: () => api.get('/api/warehouses/locations'),
  },

  operations: {
    suppliers: () => api.get('/api/operations/suppliers'),

    receipts: {
      list: (params = {}) => api.get(`/api/operations/receipts${buildQueryString(params)}`),
      get: (id) => api.get(`/api/operations/receipts/${encodeURIComponent(id)}`),
      create: (payload) => api.post('/api/operations/receipts', payload),
      update: (id, payload) => api.put(`/api/operations/receipts/${encodeURIComponent(id)}`, payload),
      ready: (id) => api.post(`/api/operations/receipts/${encodeURIComponent(id)}/ready`),
      validate: (id) => api.post(`/api/operations/receipts/${encodeURIComponent(id)}/validate`),
      cancel: (id) => api.post(`/api/operations/receipts/${encodeURIComponent(id)}/cancel`),
      remove: (id) => api.delete(`/api/operations/receipts/${encodeURIComponent(id)}`),
      slip: (id) => api.getBlob(`/api/operations/receipts/${encodeURIComponent(id)}/slip`),
    },

    deliveries: {
      list: (params = {}) => api.get(`/api/operations/deliveries${buildQueryString(params)}`),
      get: (id) => api.get(`/api/operations/deliveries/${encodeURIComponent(id)}`),
      create: (payload) => api.post('/api/operations/deliveries', payload),
      update: (id, payload) => api.put(`/api/operations/deliveries/${encodeURIComponent(id)}`, payload),
      ready: (id) => api.post(`/api/operations/deliveries/${encodeURIComponent(id)}/ready`),
      validate: (id) => api.post(`/api/operations/deliveries/${encodeURIComponent(id)}/validate`),
      cancel: (id) => api.post(`/api/operations/deliveries/${encodeURIComponent(id)}/cancel`),
      remove: (id) => api.delete(`/api/operations/deliveries/${encodeURIComponent(id)}`),
      slip: (id) => api.getBlob(`/api/operations/deliveries/${encodeURIComponent(id)}/slip`),
    },

    transfers: {
      list: (params = {}) => api.get(`/api/operations/transfers${buildQueryString(params)}`),
      get: (id) => api.get(`/api/operations/transfers/${encodeURIComponent(id)}`),
      create: (payload) => api.post('/api/operations/transfers', payload),
      validate: (id) => api.post(`/api/operations/transfers/${encodeURIComponent(id)}/validate`),
    },

    adjustments: {
      list: (params = {}) => api.get(`/api/operations/adjustments${buildQueryString(params)}`),
      create: (payload) => api.post('/api/operations/adjustments', payload),
    },
  },

  moves: {
    list: (params = {}) => api.get(`/api/moves${buildQueryString(params)}`),
    get: (id) => api.get(`/api/moves/${encodeURIComponent(id)}`),
  },
}