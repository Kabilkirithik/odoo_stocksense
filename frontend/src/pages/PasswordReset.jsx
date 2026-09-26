import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/authService'

function PasswordReset() {
  const [step, setStep] = useState(1)
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [resetToken, setResetToken] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setNotice('')

    if (step === 3 && password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setIsSubmitting(true)
    try {
      if (step === 1) {
        const message = await authService.requestOtp(email.trim())
        setNotice(message || 'A verification code was sent to your email.')
        setStep(2)
      } else if (step === 2) {
        const result = await authService.verifyOtp(email.trim(), otp)
        setResetToken(result.resetToken)
        setNotice('Email verified. Choose a new password.')
        setStep(3)
      } else if (step === 3) {
        const message = await authService.resetPassword({
          email: email.trim(),
          resetToken,
          newPassword: password,
        })
        setNotice(message || 'Password reset successfully.')
        setStep(4)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div style={styles.container}>
      <form style={styles.card} onSubmit={handleSubmit}>
        <h2 style={styles.title}>Reset Password</h2>

        {step === 1 && (
          <>
            <p style={styles.description}>Enter the email address on your account to receive a verification code.</p>
            <label style={styles.label} htmlFor="reset-email">Email address</label>
            <input
              id="reset-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              style={styles.input}
              autoComplete="email"
              required
            />
          </>
        )}

        {step === 2 && (
          <>
            <p style={styles.description}>Enter the 6-digit code sent to {email}.</p>
            <label style={styles.label} htmlFor="reset-otp">Verification code</label>
            <input
              id="reset-otp"
              type="text"
              value={otp}
              onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))}
              style={styles.input}
              inputMode="numeric"
              autoComplete="one-time-code"
              pattern="[0-9]{6}"
              maxLength={6}
              required
            />
            <button type="button" style={styles.textLink} onClick={() => { setStep(1); setNotice('') }}>
              Use a different email
            </button>
          </>
        )}

        {step === 3 && (
          <>
            <label style={styles.label} htmlFor="new-password">New password</label>
            <input
              id="new-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              style={styles.input}
              autoComplete="new-password"
              minLength={8}
              required
            />
            <label style={styles.label} htmlFor="confirm-password">Confirm new password</label>
            <input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              style={styles.input}
              autoComplete="new-password"
              minLength={8}
              required
            />
          </>
        )}

        {error && <p role="alert" style={styles.error}>{error}</p>}
        {notice && <p role="status" style={styles.notice}>{notice}</p>}

        {step < 4 ? (
          <button type="submit" style={styles.button} disabled={isSubmitting}>
            {isSubmitting ? 'Please wait...' : ['Send code', 'Verify code', 'Reset password'][step - 1]}
          </button>
        ) : (
          <button
            type="button"
            style={styles.button}
            onClick={() => navigate('/login', { state: { message: 'Password reset successfully. Sign in with your new password.' } })}
          >
            Return to login
          </button>
        )}

        {step < 4 && (
          <button type="button" style={styles.backButton} onClick={() => navigate('/login')}>
            Back to login
          </button>
        )}
      </form>
    </div>
  )
}

const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    padding: '24px',
    boxSizing: 'border-box',
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
    width: '100%',
    maxWidth: '360px',
  },
  title: { textAlign: 'center', margin: '0 0 18px' },
  description: { color: '#555', fontSize: '14px', lineHeight: 1.5, margin: '0 0 16px' },
  label: { marginBottom: '5px', fontSize: '14px' },
  input: {
    padding: '10px',
    marginBottom: '15px',
    borderRadius: '4px',
    border: '1px solid #ccc',
    fontSize: '14px',
  },
  error: { color: '#dc2626', fontSize: '13px', margin: '0 0 12px' },
  notice: { color: '#15803d', fontSize: '13px', lineHeight: 1.4, margin: '0 0 12px' },
  button: {
    padding: '10px',
    backgroundColor: '#2563eb',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '15px',
  },
  textLink: {
    alignSelf: 'flex-start',
    color: '#2563eb',
    background: 'none',
    border: 'none',
    padding: 0,
    marginBottom: '15px',
    font: 'inherit',
    cursor: 'pointer',
  },
  backButton: {
    marginTop: '12px',
    padding: '8px',
    color: '#555',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
  },
}

export default PasswordReset