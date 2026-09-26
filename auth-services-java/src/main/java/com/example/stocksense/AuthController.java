package com.example.stocksense;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.LockedException;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Consolidated REST Controller, Record DTOs, and Global Exception Handler.
 */
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

    @PostMapping("/logout")
    public ResponseEntity<ApiResponse<Void>> logout(HttpServletRequest httpRequest) {
        authService.logout(httpRequest);
        return ResponseEntity.ok(ApiResponse.success("Logged out successfully."));
    }

    @PostMapping("/forgot-password")
    public ResponseEntity<ApiResponse<Void>> forgotPassword(
            @Valid @RequestBody ForgotPasswordRequest request,
            HttpServletRequest httpRequest) {
        otpService.generateAndSendOtp(request.email(), httpRequest);
        return ResponseEntity.ok(ApiResponse.success("If an account is associated with this email, a verification code has been dispatched."));
    }

    @PostMapping("/verify-otp")
    public ResponseEntity<ApiResponse<Map<String, String>>> verifyOtp(
            @Valid @RequestBody VerifyOtpRequest request) {
        String resetToken = otpService.verifyOtp(request.email(), request.otp());
        return ResponseEntity.ok(ApiResponse.success("OTP verified successfully. You may now reset your password.",
                Map.of("resetToken", resetToken, "email", request.email())));
    }

    @PostMapping("/reset-password")
    public ResponseEntity<ApiResponse<Void>> resetPassword(
            @Valid @RequestBody ResetPasswordRequest request,
            HttpServletRequest httpRequest) {
        otpService.resetPassword(request.email(), request.resetToken(), request.newPassword(), httpRequest);
        return ResponseEntity.ok(ApiResponse.success("Password reset successfully. Please log in with your new password."));
    }

    /**
     * Dedicated Token Validation Endpoint for Python Backend.
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
            @AuthenticationPrincipal User user) {
        if (user == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error("Unauthorized"));
        }
        UserSummaryDto profile = authService.getUserProfile(user.getId());
        return ResponseEntity.ok(ApiResponse.success("Profile retrieved.", profile));
    }

    @GetMapping("/health")
    public ResponseEntity<ApiResponse<Map<String, Object>>> health() {
        return ResponseEntity.ok(ApiResponse.success("StockSense Auth Service is operational.", Map.of(
                "service", "StockSense Auth Service (Java 21 / Spring Boot)",
                "status", "UP",
                "securityEngine", "HMAC-SHA256 / BCrypt(12)",
                "integrationTarget", "Python Inventory Management Backend"
        )));
    }
}

// ============================================================================
// Record DTOs (Java 21)
// ============================================================================

record RegisterRequest(
        @NotBlank(message = "Username is required")
        @Size(min = 3, max = 64, message = "Username must be between 3 and 64 characters")
        String username,

        @NotBlank(message = "Email is required")
        @Email(message = "Invalid email format")
        String email,

        @NotBlank(message = "Password is required")
        @Size(min = 8, message = "Password must be at least 8 characters")
        String password,

        @NotBlank(message = "Full name is required")
        String fullName
) {
    public String getUsername() { return username; }
    public String getEmail() { return email; }
    public String getPassword() { return password; }
    public String getFullName() { return fullName; }
}

record LoginRequest(
        @NotBlank(message = "Username or email is required")
        String usernameOrEmail,

        @NotBlank(message = "Password is required")
        String password
) {
    public String getUsernameOrEmail() { return usernameOrEmail; }
    public String getPassword() { return password; }
}

record ForgotPasswordRequest(
        @NotBlank(message = "Email is required")
        @Email(message = "Invalid email format")
        String email
) {
    public String getEmail() { return email; }
}

record VerifyOtpRequest(
        @NotBlank(message = "Email is required")
        @Email(message = "Invalid email format")
        String email,

        @NotBlank(message = "OTP is required")
        @Pattern(regexp = "^\\d{6}$", message = "OTP must be a 6-digit number")
        String otp
) {
    public String getEmail() { return email; }
    public String getOtp() { return otp; }
}

record ResetPasswordRequest(
        @NotBlank(message = "Email is required")
        @Email(message = "Invalid email format")
        String email,

        @NotBlank(message = "Reset token is required")
        String resetToken,

        @NotBlank(message = "New password is required")
        @Size(min = 8, message = "Password must be at least 8 characters")
        String newPassword
) {
    public String getEmail() { return email; }
    public String getResetToken() { return resetToken; }
    public String getNewPassword() { return newPassword; }
}

record UserSummaryDto(
        Long id,
        String username,
        String email,
        String fullName,
        LocalDateTime createdAt
) {
    public static UserSummaryDto fromEntity(User user) {
        return new UserSummaryDto(user.getId(), user.getUsername(), user.getEmail(), user.getFullName(), user.getCreatedAt());
    }

    public Long getId() { return id; }
    public String getUsername() { return username; }
    public String getEmail() { return email; }
    public String getFullName() { return fullName; }
    public LocalDateTime getCreatedAt() { return createdAt; }
}

record AuthResponse(
        String token,
        long expiresIn,
        String dashboardUrl,
        UserSummaryDto user
) {
    public String getToken() { return token; }
    public long getExpiresIn() { return expiresIn; }
    public String getDashboardUrl() { return dashboardUrl; }
    public UserSummaryDto getUser() { return user; }
}

record TokenValidationResponse(
        boolean valid,
        String message,
        Long userId,
        String username,
        String email,
        String fullName,
        Long expiresAt
) {
    public static TokenValidationResponse valid(Long userId, String username, String email, String fullName, Long exp) {
        return new TokenValidationResponse(true, "Token is active and valid.", userId, username, email, fullName, exp);
    }

    public static TokenValidationResponse invalid(String message) {
        return new TokenValidationResponse(false, message, null, null, null, null, null);
    }

    public boolean isValid() { return valid; }
    public String getUsername() { return username; }
    public String getEmail() { return email; }
}

record ApiResponse<T>(
        boolean success,
        String message,
        T data,
        LocalDateTime timestamp
) {
    public static <T> ApiResponse<T> success(String message, T data) {
        return new ApiResponse<>(true, message, data, LocalDateTime.now());
    }

    public static <T> ApiResponse<T> success(String message) {
        return new ApiResponse<>(true, message, null, LocalDateTime.now());
    }

    public static <T> ApiResponse<T> error(String message) {
        return new ApiResponse<>(false, message, null, LocalDateTime.now());
    }
}

// ============================================================================
// Global Rest Exception Handler
// ============================================================================

@RestControllerAdvice
class RestExceptionHandler {

    @ExceptionHandler(BadCredentialsException.class)
    public ResponseEntity<ApiResponse<Void>> handleBadCredentials(BadCredentialsException ex) {
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiResponse.error(ex.getMessage()));
    }

    @ExceptionHandler(LockedException.class)
    public ResponseEntity<ApiResponse<Void>> handleLocked(LockedException ex) {
        return ResponseEntity.status(HttpStatus.LOCKED).body(ApiResponse.error(ex.getMessage()));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ApiResponse<Void>> handleIllegalArgument(IllegalArgumentException ex) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(ApiResponse.error(ex.getMessage()));
    }

    @ExceptionHandler(IllegalStateException.class)
    public ResponseEntity<ApiResponse<Void>> handleIllegalState(IllegalStateException ex) {
        return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS).body(ApiResponse.error(ex.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidation(MethodArgumentNotValidException ex) {
        String errors = ex.getBindingResult().getFieldErrors().stream()
                .map(err -> err.getField() + ": " + err.getDefaultMessage())
                .collect(Collectors.joining("; "));
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(ApiResponse.error("Validation error: " + errors));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleGeneric(Exception ex) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.error("An unexpected error occurred: " + ex.getMessage()));
    }
}
