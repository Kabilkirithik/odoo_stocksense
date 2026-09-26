const AUTH_BASE_URL = import.meta.env.VITE_AUTH_URL || 'http://35.206.93.73:8081/api/v1/auth'

async function post(path, payload) {
  let response

  try {
    response = await fetch(`${AUTH_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch {
    throw new Error('Unable to reach the authentication service. Check that it is running.')
  }

  const result = await response.json().catch(() => null)
  if (!response.ok || !result?.success) {
    throw new Error(result?.message || 'The authentication request failed.')
  }

  return result
}

function saveSession(data) {
  const token = data?.token || data?.accessToken
  if (!token) throw new Error('The authentication service did not return a session token.')

  localStorage.setItem('stocksense_token', token)
  if (data.user) localStorage.setItem('stocksense_user', JSON.stringify(data.user))
}

export const authService = {
  async login(usernameOrEmail, password) {
    const result = await post('/login', { usernameOrEmail, password })
    saveSession(result.data)
    return result.data
  },

  async register({ username, email, password, fullName }) {
    const result = await post('/register', { username, email, password, fullName })
    saveSession(result.data)
    return result.data
  },

  async requestOtp(email) {
    const result = await post('/forgot-password', { email })
    return result.message
  },

  async verifyOtp(email, otp) {
    const result = await post('/verify-otp', { email, otp: String(otp).trim() })
    return result.data
  },

  async resetPassword({ email, resetToken, newPassword }) {
    const result = await post('/reset-password', { email, resetToken, newPassword })
    return result.message
  },
}