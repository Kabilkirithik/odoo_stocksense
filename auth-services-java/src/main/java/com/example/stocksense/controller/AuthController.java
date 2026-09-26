package com.example.stocksense.controller;

import com.example.stocksense.dto.*;
import com.example.stocksense.security.CustomUserDetails;
import com.example.stocksense.service.AuthService;
import com.example.stocksense.service.OtpService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final AuthService authService;
    private final OtpService otpService;

    public AuthController(AuthService authService, OtpService otpService) {
        this.authService = authService;
        this.otpService = otpService;
    }

    @PostMapping("/register")
    public ResponseEntity<ApiResponse<AuthResponse>> register(
            @Valid @RequestBody RegisterRequest request,
            HttpServletRequest httpRequest) {
        AuthResponse response = authService.register(request, httpRequest);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("Account registered successfully.", response));
    }

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<AuthResponse>> login(
            @Valid @RequestBody LoginRequest request,
            HttpServletRequest httpRequest) {
        AuthResponse response = authService.login(request, httpRequest);
        return ResponseEntity.ok(ApiResponse.success("Login successful.", response));
    }

    @PostMapping("/refresh")
    public ResponseEntity<ApiResponse<AuthResponse>> refreshToken(
            @Valid @RequestBody RefreshTokenRequest request,
            HttpServletRequest httpRequest) {
        AuthResponse response = authService.refreshToken(request, httpRequest);
        return ResponseEntity.ok(ApiResponse.success("Token refreshed successfully.", response));
    }

    @PostMapping("/logout")
    public ResponseEntity<ApiResponse<Void>> logout(
            @RequestBody(required = false) RefreshTokenRequest request,
            HttpServletRequest httpRequest) {
        String token = request != null ? request.getRefreshToken() : null;
        authService.logout(token, httpRequest);
        return ResponseEntity.ok(ApiResponse.success("Logged out successfully."));
    }

    @PostMapping("/forgot-password")
    public ResponseEntity<ApiResponse<Void>> forgotPassword(
            @Valid @RequestBody ForgotPasswordRequest request,
            HttpServletRequest httpRequest) {
        otpService.generateAndSendOtp(request.getEmail(), httpRequest);
        return ResponseEntity.ok(ApiResponse.success("OTP has been sent to your registered email address."));
    }

    @PostMapping("/verify-otp")
    public ResponseEntity<ApiResponse<Map<String, String>>> verifyOtp(
            @Valid @RequestBody VerifyOtpRequest request) {
        String resetToken = otpService.verifyOtp(request.getEmail(), request.getOtp());
        return ResponseEntity.ok(ApiResponse.success("OTP verified successfully. You may now reset your password.",
                Map.of("resetToken", resetToken, "email", request.getEmail())));
    }

    @PostMapping("/reset-password")
    public ResponseEntity<ApiResponse<Void>> resetPassword(
            @Valid @RequestBody ResetPasswordRequest request,
            HttpServletRequest httpRequest) {
        otpService.resetPassword(request.getEmail(), request.getResetToken(), request.getNewPassword(), httpRequest);
        return ResponseEntity.ok(ApiResponse.success("Password reset successfully. Please log in with your new password."));
    }

    /**
     * Dedicated Token Validation Endpoint for the Python Inventory Management Backend
     */
    @PostMapping("/validate")
    public ResponseEntity<TokenValidationResponse> validateToken(
            @RequestBody(required = false) Map<String, String> payload,
            @RequestHeader(value = "Authorization", required = false) String authHeader) {

        String token = null;
        if (payload != null && payload.containsKey("token")) {
            token = payload.get("token");
        } else if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        if (token == null || token.isBlank()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(TokenValidationResponse.invalid("No token provided."));
        }

        TokenValidationResponse validation = authService.validateTokenForBackend(token);
        if (validation.isValid()) {
            return ResponseEntity.ok(validation);
        } else {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(validation);
        }
    }

    @GetMapping("/me")
    public ResponseEntity<ApiResponse<UserSummaryDto>> getCurrentUser(
            @AuthenticationPrincipal CustomUserDetails userDetails) {
        if (userDetails == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error("Unauthorized"));
        }
        UserSummaryDto profile = authService.getUserProfile(userDetails.getId());
        return ResponseEntity.ok(ApiResponse.success("Profile retrieved.", profile));
    }

    @GetMapping("/health")
    public ResponseEntity<ApiResponse<Map<String, Object>>> health() {
        return ResponseEntity.ok(ApiResponse.success("StockSense Auth Service is operational.", Map.of(
                "service", "StockSense Auth Service (Java/Spring Boot)",
                "status", "UP",
                "securityEngine", "HMAC-SHA256 / BCrypt(12)",
                "integrationTarget", "Python Inventory Management Backend"
        )));
    }
}
