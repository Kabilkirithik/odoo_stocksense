package com.example.stocksense.service;

import com.example.stocksense.dto.*;
import com.example.stocksense.entity.RefreshToken;
import com.example.stocksense.entity.User;
import com.example.stocksense.repository.RefreshTokenRepository;
import com.example.stocksense.repository.UserRepository;
import com.example.stocksense.security.JwtService;
import com.example.stocksense.security.RateLimiterService;
import com.example.stocksense.security.SecurityAuditService;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.LockedException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDateTime;
import java.util.Base64;
import java.util.Map;
import java.util.Optional;

@Service
public class AuthService {

    private static final Logger logger = LoggerFactory.getLogger(AuthService.class);
    private static final SecureRandom secureRandom = new SecureRandom();
    private static final int MAX_FAILED_ATTEMPTS = 5;
    private static final long LOCK_TIME_DURATION_MINUTES = 15;

    private final UserRepository userRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final SecurityAuditService auditService;
    private final RateLimiterService rateLimiterService;

    private final long refreshTokenExpirationDays;
    private final String inventoryDashboardUrl;

    public AuthService(
            UserRepository userRepository,
            RefreshTokenRepository refreshTokenRepository,
            PasswordEncoder passwordEncoder,
            JwtService jwtService,
            SecurityAuditService auditService,
            RateLimiterService rateLimiterService,
            @Value("${app.jwt.refresh-token-expiration-days:7}") long refreshTokenExpirationDays,
            @Value("${app.inventory.dashboard-url:http://localhost:8000/dashboard}") String inventoryDashboardUrl) {
        this.userRepository = userRepository;
        this.refreshTokenRepository = refreshTokenRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.auditService = auditService;
        this.rateLimiterService = rateLimiterService;
        this.refreshTokenExpirationDays = refreshTokenExpirationDays;
        this.inventoryDashboardUrl = inventoryDashboardUrl;
    }

    @Transactional
    public AuthResponse register(RegisterRequest request, HttpServletRequest httpRequest) {
        String clientIp = auditService.extractClientIp(httpRequest);
        if (!rateLimiterService.isAllowed("register_" + clientIp)) {
            throw new IllegalStateException("Too many registration attempts. Please try again later.");
        }

        String username = request.getUsername().trim().toLowerCase();
        String email = request.getEmail().trim().toLowerCase();

        if (userRepository.existsByUsername(username)) {
            throw new IllegalArgumentException("Username is already taken.");
        }

        if (userRepository.existsByEmail(email)) {
            throw new IllegalArgumentException("An account with this email already exists.");
        }

        User user = new User(
                username,
                email,
                passwordEncoder.encode(request.getPassword()),
                request.getFullName().trim()
        );

        User savedUser = userRepository.save(user);

        // Generate tokens
        String accessToken = jwtService.generateAccessToken(savedUser);
        RefreshToken refreshToken = createRefreshToken(savedUser);

        auditService.recordEvent(savedUser.getUsername(), "REGISTER_SUCCESS", httpRequest, "User account registered successfully");

        return new AuthResponse(
                accessToken,
                refreshToken.getToken(),
                jwtService.getAccessTokenExpirationSeconds(),
                inventoryDashboardUrl,
                UserSummaryDto.fromEntity(savedUser)
        );
    }

    @Transactional
    public AuthResponse login(LoginRequest request, HttpServletRequest httpRequest) {
        String clientIp = auditService.extractClientIp(httpRequest);
        if (!rateLimiterService.isAllowed("login_" + clientIp)) {
            throw new IllegalStateException("Too many login attempts. Please try again in a minute.");
        }

        String identifier = request.getUsernameOrEmail().trim().toLowerCase();
        Optional<User> userOptional = userRepository.findByEmailOrUsername(identifier, identifier);

        if (userOptional.isEmpty()) {
            auditService.recordEvent(identifier, "LOGIN_FAILED", httpRequest, "Invalid user identifier");
            throw new BadCredentialsException("Invalid username/email or password.");
        }

        User user = userOptional.get();

        // Check if account is locked
        if (!user.isAccountNonLocked()) {
            if (user.getLockTime() != null) {
                LocalDateTime unlockTime = user.getLockTime().plusMinutes(LOCK_TIME_DURATION_MINUTES);
                if (LocalDateTime.now().isAfter(unlockTime)) {
                    // Unlock account automatically after lock duration has passed
                    user.setAccountNonLocked(true);
                    user.setFailedLoginAttempts(0);
                    user.setLockTime(null);
                    userRepository.save(user);
                } else {
                    long minutesRemaining = Duration.between(LocalDateTime.now(), unlockTime).toMinutes() + 1;
                    throw new LockedException("Account is temporarily locked due to multiple failed login attempts. Try again in " + minutesRemaining + " minutes or reset your password.");
                }
            } else {
                throw new LockedException("Account is locked. Please reset your password or contact support.");
            }
        }

        // Verify password
        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            int failedAttempts = user.getFailedLoginAttempts() + 1;
            user.setFailedLoginAttempts(failedAttempts);

            if (failedAttempts >= MAX_FAILED_ATTEMPTS) {
                user.setAccountNonLocked(false);
                user.setLockTime(LocalDateTime.now());
                userRepository.save(user);
                auditService.recordEvent(user.getUsername(), "ACCOUNT_LOCKED", httpRequest, "Account locked after " + failedAttempts + " failed attempts");
                throw new LockedException("Maximum login attempts exceeded. Account is locked for " + LOCK_TIME_DURATION_MINUTES + " minutes. Use OTP Password Reset to unlock immediately.");
            }

            userRepository.save(user);
            int remaining = MAX_FAILED_ATTEMPTS - failedAttempts;
            auditService.recordEvent(user.getUsername(), "LOGIN_FAILED", httpRequest, "Bad credentials (" + remaining + " attempts remaining)");
            throw new BadCredentialsException("Invalid username/email or password. " + remaining + " attempt(s) remaining.");
        }

        // Credentials are valid: Reset failed attempts
        if (user.getFailedLoginAttempts() > 0) {
            user.setFailedLoginAttempts(0);
            user.setLockTime(null);
            userRepository.save(user);
        }

        // Generate tokens
        String accessToken = jwtService.generateAccessToken(user);
        RefreshToken refreshToken = createRefreshToken(user);

        auditService.recordEvent(user.getUsername(), "LOGIN_SUCCESS", httpRequest, "Successful authentication");

        return new AuthResponse(
                accessToken,
                refreshToken.getToken(),
                jwtService.getAccessTokenExpirationSeconds(),
                inventoryDashboardUrl,
                UserSummaryDto.fromEntity(user)
        );
    }

    @Transactional
    public AuthResponse refreshToken(RefreshTokenRequest request, HttpServletRequest httpRequest) {
        String tokenStr = request.getRefreshToken();
        RefreshToken refreshToken = refreshTokenRepository.findByToken(tokenStr)
                .orElseThrow(() -> new IllegalArgumentException("Invalid refresh token."));

        User user = refreshToken.getUser();

        // Check for Token Reuse Attack
        if (refreshToken.isRevoked()) {
            logger.warn("SECURITY ALERT: Compromised refresh token reuse detected for user {}. Revoking all sessions!", user.getUsername());
            refreshTokenRepository.revokeAllByUser(user);
            auditService.recordEvent(user.getUsername(), "TOKEN_REUSE_DETECTED", httpRequest, "Refresh token reuse attempt - all sessions invalidated");
            throw new IllegalStateException("Security alert: Token reuse detected. Please log in again.");
        }

        if (refreshToken.isExpired()) {
            throw new IllegalArgumentException("Refresh token has expired. Please log in again.");
        }

        // Token rotation: Revoke current refresh token and generate a new one
        refreshToken.setRevoked(true);
        refreshTokenRepository.save(refreshToken);

        RefreshToken newRefreshToken = createRefreshToken(user);
        String newAccessToken = jwtService.generateAccessToken(user);

        return new AuthResponse(
                newAccessToken,
                newRefreshToken.getToken(),
                jwtService.getAccessTokenExpirationSeconds(),
                inventoryDashboardUrl,
                UserSummaryDto.fromEntity(user)
        );
    }

    @Transactional
    public void logout(String refreshTokenStr, HttpServletRequest httpRequest) {
        if (refreshTokenStr != null && !refreshTokenStr.isBlank()) {
            refreshTokenRepository.findByToken(refreshTokenStr).ifPresent(token -> {
                token.setRevoked(true);
                refreshTokenRepository.save(token);
                auditService.recordEvent(token.getUser().getUsername(), "LOGOUT", httpRequest, "User logged out");
            });
        }
    }

    @Transactional(readOnly = true)
    public TokenValidationResponse validateTokenForBackend(String token) {
        if (!jwtService.validateToken(token)) {
            return TokenValidationResponse.invalid("Invalid, expired, or tampered token.");
        }

        Long userId = jwtService.getUserIdFromToken(token);
        if (userId == null) {
            return TokenValidationResponse.invalid("Missing user identity claim in token.");
        }

        Optional<User> userOpt = userRepository.findById(userId);
        if (userOpt.isEmpty() || !userOpt.get().isEnabled() || !userOpt.get().isAccountNonLocked()) {
            return TokenValidationResponse.invalid("User account is inactive or locked.");
        }

        User user = userOpt.get();
        Map<String, Object> claims = jwtService.getClaims(token);
        Long exp = claims != null && claims.get("exp") instanceof Number n ? n.longValue() : null;

        return TokenValidationResponse.valid(
                user.getId(),
                user.getUsername(),
                user.getEmail(),
                user.getFullName(),
                exp
        );
    }

    @Transactional(readOnly = true)
    public UserSummaryDto getUserProfile(Long userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found"));
        return UserSummaryDto.fromEntity(user);
    }

    public String getInventoryDashboardUrl() {
        return inventoryDashboardUrl;
    }

    private RefreshToken createRefreshToken(User user) {
        byte[] randomBytes = new byte[64];
        secureRandom.nextBytes(randomBytes);
        String tokenString = Base64.getUrlEncoder().withoutPadding().encodeToString(randomBytes);

        Instant expiryDate = Instant.now().plus(Duration.ofDays(refreshTokenExpirationDays));
        RefreshToken refreshToken = new RefreshToken(tokenString, user, expiryDate);
        return refreshTokenRepository.save(refreshToken);
    }
}
