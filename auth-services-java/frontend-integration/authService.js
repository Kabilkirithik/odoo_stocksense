/**
 * StockSense Authentication Service - JavaScript Client
 * 
 * Drop-in helper module for frontend applications (React, Vue, Vanilla JS, Vite, Next.js).
 * Handles user signup, login, OTP password reset flow, token persistence, and API calls.
 */

const AUTH_BASE_URL = process?.env?.REACT_APP_AUTH_URL ||
                      process?.env?.VITE_AUTH_URL ||
                      'http://localhost:8081/api/v1/auth';

const TOKEN_KEY = 'stocksense_token';
const USER_KEY = 'stocksense_user';

class StockSenseAuth {
  /**
   * 1. Sign Up (Register a new user)
   * Automatically saves token and returns data with dashboard redirect URL.
   */
  static async register({ username, email, password, fullName }) {
    const response = await fetch(`${AUTH_BASE_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password, fullName })
    });
    const result = await response.json();

    if (!response.ok || !result.success) {
      throw new Error(result.message || 'Registration failed.');
    }

    // Persist session token
    StockSenseAuth.saveSession(result.data);
    return result.data;
  }

  /**
   * 2. Sign In (Login with username/email and password)
   * Saves token and returns data containing the Inventory Dashboard redirectUrl.
   */
  static async login({ usernameOrEmail, password }) {
    const response = await fetch(`${AUTH_BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usernameOrEmail, password })
    });
    const result = await response.json();

    if (!response.ok || !result.success) {
      const error = new Error(result.message || 'Login failed.');
      error.status = response.status;
      error.details = result.data;
      throw error;
    }

    // Persist session token
    StockSenseAuth.saveSession(result.data);
    return result.data;
  }

  /**
   * 3. OTP Flow - Step 1: Request Password Reset OTP
   * Sends 6-digit numeric OTP to the user's email.
   */
  static async requestOtp(email) {
    const response = await fetch(`${AUTH_BASE_URL}/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const result = await response.json();

    if (!response.ok || !result.success) {
      throw new Error(result.message || 'Failed to send OTP.');
    }
    return result.message;
  }

  /**
   * 3. OTP Flow - Step 2: Verify OTP
   * Submits 6-digit OTP code. Returns a one-time resetToken needed for Step 3.
   */
  static async verifyOtp(email, otp) {
    const response = await fetch(`${AUTH_BASE_URL}/verify-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp: otp.trim() })
    });
    const result = await response.json();

    if (!response.ok || !result.success) {
      throw new Error(result.message || 'Invalid or expired OTP.');
    }
    return result.data;
  }

  /**
   * 3. OTP Flow - Step 3: Set New Password
   * Sets new password using the resetToken from Step 2.
   */
  static async resetPassword({ email, resetToken, newPassword }) {
    const response = await fetch(`${AUTH_BASE_URL}/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, resetToken, newPassword })
    });
    const result = await response.json();

    if (!response.ok || !result.success) {
      throw new Error(result.message || 'Password reset failed.');
    }
    return result.message;
  }

  /**
   * 4. Logout (Stateless client token removal)
   */
  static async logout() {
    try {
      await fetch(`${AUTH_BASE_URL}/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (_) {
      // Ignore network errors on logout
    } finally {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
  }

  /**
   * 5. Authenticated fetch wrapper
   * Automatically adds 'Authorization: Bearer <token>' to any backend request
   * (e.g. calls to Python Inventory Backend at http://localhost:8000).
   */
  static async authFetch(url, options = {}) {
    let token = StockSenseAuth.getToken();

    options.headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    };

    let response = await fetch(url, options);

    if (response.status === 401) {
      StockSenseAuth.logout();
      window.location.href = '/login';
    }

    return response;
  }

  // --- Session Storage Helpers ---

  static saveSession(authData) {
    const token = authData.token || authData.accessToken;
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    }
    if (authData.user) {
      localStorage.setItem(USER_KEY, JSON.stringify(authData.user));
    }
  }

  static getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  static getCurrentUser() {
    const userStr = localStorage.getItem(USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }

  static isAuthenticated() {
    return !!StockSenseAuth.getToken();
  }
}

export default StockSenseAuth;
if (typeof module !== 'undefined') {
  module.exports = StockSenseAuth;
}
