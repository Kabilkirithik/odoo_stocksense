/**
 * StockSense Authentication Service - Universal JavaScript Client SDK
 * 
 * Drop-in module for frontend frameworks (React, Vue, Next.js, Vite, Angular, Vanilla JS).
 * Handles:
 * - User Registration & Login
 * - Automatic Dashboard Redirection URL resolution
 * - OTP 3-step Password Recovery
 * - Stateless JWT Token Storage & Session Management
 * - Bearer Token Authenticated Fetch Interceptor (for Python Inventory Backend)
 * - Profile and Health Checks
 */

const getBaseUrl = () => {
  if (typeof process !== 'undefined' && process.env) {
    if (process.env.VITE_AUTH_URL) return process.env.VITE_AUTH_URL;
    if (process.env.NEXT_PUBLIC_AUTH_URL) return process.env.NEXT_PUBLIC_AUTH_URL;
    if (process.env.REACT_APP_AUTH_URL) return process.env.REACT_APP_AUTH_URL;
  }
  if (typeof window !== 'undefined' && window.__STOCKSENSE_AUTH_URL__) {
    return window.__STOCKSENSE_AUTH_URL__;
  }
  return 'http://localhost:8081/api/v1/auth';
};

const AUTH_BASE_URL = getBaseUrl();
const TOKEN_KEY = 'stocksense_token';
const USER_KEY = 'stocksense_user';

class StockSenseAuth {
  /**
   * 1. Register a new user
   * Automatically persists token and returns data including target dashboardUrl / redirectUrl.
   * @param {Object} params - { username, email, password, fullName }
   * @returns {Promise<Object>} auth payload with token, user, and dashboardUrl
   */
  static async register({ username, email, password, fullName }) {
    const response = await fetch(`${AUTH_BASE_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password, fullName })
    });
    const result = await response.json();

    if (!response.ok || !result.success) {
      const error = new Error(result.message || 'Registration failed.');
      error.status = response.status;
      error.data = result.data;
      throw error;
    }

    if (result.data) {
      result.data.redirectUrl = result.data.dashboardUrl || result.data.redirectUrl;
      StockSenseAuth.saveSession(result.data);
    }
    return result.data;
  }

  /**
   * 2. Sign In with username/email and password
   * Automatically persists token and returns data with dashboardUrl / redirectUrl.
   * @param {Object} params - { usernameOrEmail, password }
   * @returns {Promise<Object>} auth payload with token, user, and dashboardUrl
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
      error.data = result.data;
      throw error;
    }

    if (result.data) {
      result.data.redirectUrl = result.data.dashboardUrl || result.data.redirectUrl;
      StockSenseAuth.saveSession(result.data);
    }
    return result.data;
  }

  /**
   * 3. OTP Password Reset - Step 1: Request OTP
   * Sends 6-digit numeric OTP to the user's email.
   * @param {string} email
   * @returns {Promise<string>} Success message
   */
  static async requestOtp(email) {
    const response = await fetch(`${AUTH_BASE_URL}/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const result = await response.json();

    if (!response.ok || !result.success) {
      const error = new Error(result.message || 'Failed to dispatch OTP.');
      error.status = response.status;
      throw error;
    }
    return result.message;
  }

  /**
   * 3. OTP Password Reset - Step 2: Verify OTP
   * Submits 6-digit code. Returns a single-use resetToken for Step 3.
   * @param {string} email
   * @param {string} otp (6 numeric digits)
   * @returns {Promise<{ resetToken: string, email: string }>}
   */
  static async verifyOtp(email, otp) {
    const response = await fetch(`${AUTH_BASE_URL}/verify-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp: String(otp).trim() })
    });
    const result = await response.json();

    if (!response.ok || !result.success) {
      const error = new Error(result.message || 'Invalid or expired OTP.');
      error.status = response.status;
      throw error;
    }
    return result.data;
  }

  /**
   * 3. OTP Password Reset - Step 3: Set New Password
   * Sets new password using the resetToken from Step 2.
   * @param {Object} params - { email, resetToken, newPassword }
   * @returns {Promise<string>} Success message
   */
  static async resetPassword({ email, resetToken, newPassword }) {
    const response = await fetch(`${AUTH_BASE_URL}/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, resetToken, newPassword })
    });
    const result = await response.json();

    if (!response.ok || !result.success) {
      const error = new Error(result.message || 'Password reset failed.');
      error.status = response.status;
      throw error;
    }
    return result.message;
  }

  /**
   * 4. Fetch Current User Profile
   * @returns {Promise<Object>} User details (id, username, email, fullName, createdAt)
   */
  static async getProfile() {
    const token = StockSenseAuth.getToken();
    if (!token) throw new Error('Not authenticated');

    const response = await fetch(`${AUTH_BASE_URL}/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    const result = await response.json();

    if (!response.ok || !result.success) {
      if (response.status === 401) StockSenseAuth.clearSession();
      throw new Error(result.message || 'Failed to fetch user profile.');
    }

    if (result.data) {
      localStorage.setItem(USER_KEY, JSON.stringify(result.data));
    }
    return result.data;
  }

  /**
   * 5. Check Health of Auth Service
   * @returns {Promise<Object>}
   */
  static async checkHealth() {
    const response = await fetch(`${AUTH_BASE_URL}/health`);
    return response.json();
  }

  /**
   * 6. Logout
   * Clears stored JWT token and cached user session from localStorage.
   */
  static async logout() {
    try {
      await fetch(`${AUTH_BASE_URL}/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (_) {
      // Ignore network errors during logout
    } finally {
      StockSenseAuth.clearSession();
    }
  }

  /**
   * 7. Authenticated Fetch Helper
   * Automatically adds 'Authorization: Bearer <token>' to any backend request
   * (e.g. calls to the Python Inventory Backend at http://localhost:8000).
   * Automatically clears session and redirects to /login on HTTP 401.
   */
  static async authFetch(url, options = {}) {
    const token = StockSenseAuth.getToken();
    options.headers = {
      ...(options.headers || {}),
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };

    const response = await fetch(url, options);

    if (response.status === 401 && typeof window !== 'undefined') {
      StockSenseAuth.clearSession();
      window.location.href = '/login';
    }

    return response;
  }

  // --- Session Storage Management ---

  static saveSession(authData) {
    if (typeof localStorage === 'undefined') return;
    const token = authData.token || authData.accessToken;
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    }
    if (authData.user) {
      localStorage.setItem(USER_KEY, JSON.stringify(authData.user));
    }
  }

  static clearSession() {
    if (typeof localStorage === 'undefined') return;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  static getToken() {
    if (typeof localStorage === 'undefined') return null;
    return localStorage.getItem(TOKEN_KEY);
  }

  static getCurrentUser() {
    if (typeof localStorage === 'undefined') return null;
    const userStr = localStorage.getItem(USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }

  static isAuthenticated() {
    return !!StockSenseAuth.getToken();
  }
}

export default StockSenseAuth;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = StockSenseAuth;
}
