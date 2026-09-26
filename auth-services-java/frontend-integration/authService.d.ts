/**
 * TypeScript Type Definitions for StockSenseAuth JavaScript SDK
 */

export interface UserSummary {
  id: number;
  username: string;
  email: string;
  fullName: string;
  createdAt: string;
}

export interface AuthResponseData {
  token: string;
  expiresIn: number;
  dashboardUrl: string;
  redirectUrl: string;
  user: UserSummary;
}

export interface RegisterParams {
  username: string;
  email: string;
  password: string;
  fullName: string;
}

export interface LoginParams {
  usernameOrEmail: string;
  password: string;
}

export interface VerifyOtpResult {
  resetToken: string;
  email: string;
}

export interface ResetPasswordParams {
  email: string;
  resetToken: string;
  newPassword: string;
}

export interface HealthCheckData {
  service: string;
  status: string;
  integrationTarget: string;
  securityEngine: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  timestamp: string;
}

export class StockSenseAuth {
  static register(params: RegisterParams): Promise<AuthResponseData>;
  static login(params: LoginParams): Promise<AuthResponseData>;
  static requestOtp(email: string): Promise<string>;
  static verifyOtp(email: string, otp: string | number): Promise<VerifyOtpResult>;
  static resetPassword(params: ResetPasswordParams): Promise<string>;
  static getProfile(): Promise<UserSummary>;
  static checkHealth(): Promise<ApiResponse<HealthCheckData>>;
  static logout(): Promise<void>;
  static authFetch(url: string, options?: RequestInit): Promise<Response>;

  static saveSession(authData: Partial<AuthResponseData>): void;
  static clearSession(): void;
  static getToken(): string | null;
  static getCurrentUser(): UserSummary | null;
  static isAuthenticated(): boolean;
}

export default StockSenseAuth;
