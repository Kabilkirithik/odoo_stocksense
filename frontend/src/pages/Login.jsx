// src/pages/Login.jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

function Login() {
  const [loginId, setLoginId] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()

  const handleSubmit = (e) => {
    e.preventDefault()
    console.log('Login ID:', loginId, 'Password:', password)
    // TODO: connect to backend auth API
    navigate('/dashboard')
  }

  return (
    <div style={styles.container}>
      <form style={styles.card} onSubmit={handleSubmit}>
        <h2 style={styles.title}>Login</h2>

        <label style={styles.label}>Login Id</label>
        <input
          type="text"
          value={loginId}
          onChange={(e) => setLoginId(e.target.value)}
          style={styles.input}
          placeholder="Enter Login Id"
          required
        />

        <label style={styles.label}>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={styles.input}
          placeholder="Enter Password"
          required
        />

        <button type="submit" style={styles.button}>
          Sign In
        </button>

        <p style={styles.forgotText}>
          Forgot Password? <span style={styles.link}>Click here</span>
        </p>

        <p style={styles.footerText}>
          Don't have an account?{' '}
          <span style={styles.link} onClick={() => navigate('/signup')}>
            Sign up
          </span>
        </p>
      </form>
    </div>
  )
}

const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    backgroundColor: '#f5f5f5',
    fontFamily: 'Arial, sans-serif',
  },
  card: {
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#fff',
    padding: '30px',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
    width: '300px',
  },
  title: { textAlign: 'center', marginBottom: '20px' },
  label: { marginBottom: '5px', fontSize: '14px' },
  input: {
    padding: '8px',
    marginBottom: '15px',
    borderRadius: '4px',
    border: '1px solid #ccc',
    fontSize: '14px',
  },
  button: {
    padding: '10px',
    backgroundColor: '#2563eb',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '15px',
  },
  forgotText: {
    textAlign: 'center',
    marginTop: '15px',
    fontSize: '13px',
  },
  footerText: {
    textAlign: 'center',
    marginTop: '8px',
    fontSize: '13px',
  },
  link: {
    color: '#2563eb',
    cursor: 'pointer',
  },
}

export default Login