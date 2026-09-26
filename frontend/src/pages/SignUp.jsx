// src/pages/SignUp.jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

function SignUp() {
  const [loginId, setLoginId] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    console.log('Sign Up:', { loginId, email, password })
    // TODO: connect to backend signup API
    navigate('/login')
  }

  return (
    <div style={styles.container}>
      <form style={styles.card} onSubmit={handleSubmit}>
        <h2 style={styles.title}>Sign Up</h2>

        <label style={styles.label}>Enter Login Id</label>
        <input
          type="text"
          value={loginId}
          onChange={(e) => setLoginId(e.target.value)}
          style={styles.input}
          placeholder="Enter Login Id"
          required
        />

        <label style={styles.label}>Enter Email Id</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={styles.input}
          placeholder="Enter Email Id"
          required
        />

        <label style={styles.label}>Enter Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={styles.input}
          placeholder="Enter Password"
          required
        />

        <label style={styles.label}>Re-enter Password</label>
        <input
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          style={styles.input}
          placeholder="Re-enter Password"
          required
        />

        {error && <p style={styles.errorText}>{error}</p>}

        <button type="submit" style={styles.button}>
          Sign Up
        </button>

        <p style={styles.footerText}>
          Already have an account?{' '}
          <span style={styles.link} onClick={() => navigate('/login')}>
            Login here
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
  errorText: {
    color: '#dc2626',
    fontSize: '13px',
    marginBottom: '10px',
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
  footerText: {
    textAlign: 'center',
    marginTop: '15px',
    fontSize: '13px',
  },
  link: {
    color: '#2563eb',
    cursor: 'pointer',
  },
}

export default SignUp