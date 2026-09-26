package com.example.stocksense;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import jakarta.mail.internet.MimeMessage;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.LockedException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Consolidated Core Authentication Service.
 * Manages user signup, login with timing-attack mitigation, brute-force lockout,
 * stateless JWT generation, and token validation for Python backend.
 */
@Service
public class AuthService {

    private static final Logger logger = LoggerFactory.getLogger(AuthService.class);
    private static final int MAX_FAILED_ATTEMPTS = 5;
    private static final long LOCK_TIME_DURATION_MINUTES = 15;

    // Pre-computed BCrypt dummy hash to enforce constant-time verification for non-existent users
    private static final String DUMMY_BCRYPT_HASH = "$2a$12$uq4R7QG4v5vT7jQG4v5vTuq4R7QG4v5vT7jQG4v5vTuq4R7QG4v5v";

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenService jwtTokenService;
    private final RateLimiter rateLimiter;
    private final String inventoryDashboardUrl;

    public AuthService(
            UserRepository userRepository,
            PasswordEncoder passwordEncoder,
            JwtTokenService jwtTokenService,
            RateLimiter rateLimiter,
            @Value("${app.inventory.dashboard-url:http://localhost:8000/dashboard}") String inventoryDashboardUrl) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenService = jwtTokenService;
        this.rateLimiter = rateLimiter;
        this.inventoryDashboardUrl = inventoryDashboardUrl;
    }

    @Transactional
    public AuthResponse register(RegisterRequest request, HttpServletRequest httpRequest) {
        String clientIp = extractClientIp(httpRequest);
        if (!rateLimiter.isAllowed("register_" + clientIp)) {
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
        String token = jwtTokenService.generateToken(savedUser);

        recordAudit(savedUser.getUsername(), "REGISTER_SUCCESS", clientIp, "User account registered successfully");

        return new AuthResponse(
                token,
                jwtTokenService.getExpirationSeconds(),
                inventoryDashboardUrl,
                UserSummaryDto.fromEntity(savedUser)
        );
    }

    @Transactional
    public AuthResponse login(LoginRequest request, HttpServletRequest httpRequest) {
        String clientIp = extractClientIp(httpRequest);
        if (!rateLimiter.isAllowed("login_" + clientIp)) {
            throw new IllegalStateException("Too many login attempts. Please try again in a minute.");
        }

        String identifier = request.getUsernameOrEmail().trim().toLowerCase();
        Optional<User> userOptional = userRepository.findByEmailOrUsername(identifier, identifier);

        if (userOptional.isEmpty()) {
            // Mitigate timing attack: compute dummy hash verification to equalize response latency
            passwordEncoder.matches(request.getPassword(), DUMMY_BCRYPT_HASH);
            recordAudit(identifier, "LOGIN_FAILED", clientIp, "Invalid user identifier");
            throw new BadCredentialsException("Invalid username/email or password.");
        }

        User user = userOptional.get();

        // Check if account is locked
        if (!user.isAccountNonLocked()) {
            if (user.getLockTime() != null) {
                LocalDateTime unlockTime = user.getLockTime().plusMinutes(LOCK_TIME_DURATION_MINUTES);
                if (LocalDateTime.now().isAfter(unlockTime)) {
                    user.setAccountNonLocked(true);
                    user.setFailedLoginAttempts(0);
                    user.setLockTime(null);
                    userRepository.save(user);
                } else {
                    long minutesRemaining = Duration.between(LocalDateTime.now(), unlockTime).toMinutes() + 1;
                    throw new LockedException("Account is temporarily locked. Try again in " + minutesRemaining + " minutes or reset your password.");
                }
            } else {
                throw new LockedException("Account is locked. Please reset your password.");
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
                recordAudit(user.getUsername(), "ACCOUNT_LOCKED", clientIp, "Account locked after " + failedAttempts + " failed attempts");
                throw new LockedException("Maximum login attempts exceeded. Account is locked for " + LOCK_TIME_DURATION_MINUTES + " minutes. Use OTP Password Reset to unlock immediately.");
            }

            userRepository.save(user);
            int remaining = MAX_FAILED_ATTEMPTS - failedAttempts;
            recordAudit(user.getUsername(), "LOGIN_FAILED", clientIp, "Bad credentials (" + remaining + " attempts remaining)");
            throw new BadCredentialsException("Invalid username/email or password. " + remaining + " attempt(s) remaining.");
        }

        // Credentials are valid: Reset failed attempts counter
        if (user.getFailedLoginAttempts() > 0) {
            user.setFailedLoginAttempts(0);
            user.setLockTime(null);
            userRepository.save(user);
        }

        String token = jwtTokenService.generateToken(user);
        recordAudit(user.getUsername(), "LOGIN_SUCCESS", clientIp, "Successful authentication");

        return new AuthResponse(
                token,
                jwtTokenService.getExpirationSeconds(),
                inventoryDashboardUrl,
                UserSummaryDto.fromEntity(user)
        );
    }

    public void logout(HttpServletRequest httpRequest) {
        recordAudit(null, "LOGOUT", extractClientIp(httpRequest), "User logged out");
    }

    @Transactional(readOnly = true)
    public TokenValidationResponse validateTokenForBackend(String token) {
        if (!jwtTokenService.validateToken(token)) {
            return TokenValidationResponse.invalid("Invalid, expired, or tampered token.");
        }

        Long userId = jwtTokenService.getUserId(token);
        if (userId == null) {
            return TokenValidationResponse.invalid("Missing user identity claim in token.");
        }

        Optional<User> userOpt = userRepository.findById(userId);
        if (userOpt.isEmpty() || !userOpt.get().isEnabled() || !userOpt.get().isAccountNonLocked()) {
            return TokenValidationResponse.invalid("User account is inactive or locked.");
        }

        User user = userOpt.get();
        Map<String, Object> claims = jwtTokenService.getClaims(token);
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

    public String extractClientIp(HttpServletRequest request) {
        if (request == null) return "127.0.0.1";
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isBlank() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("X-Real-IP");
        }
        if (ip == null || ip.isBlank() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getRemoteAddr();
        }
        return (ip != null && ip.contains(",")) ? ip.split(",")[0].trim() : ip;
    }

    private void recordAudit(String principal, String action, String clientIp, String details) {
        logger.info("[AUDIT] Action: {} | Principal: {} | Client IP: {} | Details: {}",
                action, principal != null ? principal : "ANONYMOUS", clientIp, details);
    }
}

/**
 * High-performance, In-Memory OTP and Reset-Token Store.
 * Provides restart-survivability via lightweight serialization and automatic self-cleaning.
 */
@Component
class InMemoryOtpStore {

    private static final Logger logger = LoggerFactory.getLogger(InMemoryOtpStore.class);
    private static final Path SNAPSHOT_FILE = Paths.get(".stocksense_otp_cache.ser");

    private final ConcurrentHashMap<String, OtpSession> otpCache = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, ResetSession> resetTokenCache = new ConcurrentHashMap<>();

    public static class OtpSession implements Serializable {
        @Serial
        private static final long serialVersionUID = 1L;

        private final String otpHash;
        private final Instant expiryDate;
        private final Instant createdAt;
        private int attempts;

        public OtpSession(String otpHash, Instant expiryDate) {
            this.otpHash = otpHash;
            this.expiryDate = expiryDate;
            this.createdAt = Instant.now();
            this.attempts = 0;
        }

        public String getOtpHash() { return otpHash; }
        public Instant getExpiryDate() { return expiryDate; }
        public Instant getCreatedAt() { return createdAt; }
        public int getAttempts() { return attempts; }
        public void incrementAttempts() { this.attempts++; }
        public boolean isExpired() { return Instant.now().isAfter(expiryDate); }
    }

    public static class ResetSession implements Serializable {
        @Serial
        private static final long serialVersionUID = 1L;

        private final Long userId;
        private final String email;
        private final Instant expiryDate;

        public ResetSession(Long userId, String email, Instant expiryDate) {
            this.userId = userId;
            this.email = email;
            this.expiryDate = expiryDate;
        }

        public Long getUserId() { return userId; }
        public String getEmail() { return email; }
        public Instant getExpiryDate() { return expiryDate; }
        public boolean isExpired() { return Instant.now().isAfter(expiryDate); }
    }

    public void saveOtp(String email, String otpHash, Instant expiryDate) {
        otpCache.put(email.toLowerCase().trim(), new OtpSession(otpHash, expiryDate));
    }

    public OtpSession getOtp(String email) {
        String key = email.toLowerCase().trim();
        OtpSession session = otpCache.get(key);
        if (session != null && session.isExpired()) {
            otpCache.remove(key);
            return null;
        }
        return session;
    }

    public void removeOtp(String email) {
        otpCache.remove(email.toLowerCase().trim());
    }

    public Long getSecondsSinceLastOtp(String email) {
        OtpSession session = otpCache.get(email.toLowerCase().trim());
        return session != null ? Duration.between(session.getCreatedAt(), Instant.now()).getSeconds() : null;
    }

    public void saveResetToken(String resetToken, Long userId, String email, Instant expiryDate) {
        resetTokenCache.put(resetToken, new ResetSession(userId, email.toLowerCase().trim(), expiryDate));
    }

    public ResetSession getResetSession(String resetToken) {
        ResetSession session = resetTokenCache.get(resetToken);
        if (session != null && session.isExpired()) {
            resetTokenCache.remove(resetToken);
            return null;
        }
        return session;
    }

    public void removeResetToken(String resetToken) {
        resetTokenCache.remove(resetToken);
    }

    public void clear() {
        otpCache.clear();
        resetTokenCache.clear();
        try {
            Files.deleteIfExists(SNAPSHOT_FILE);
        } catch (Exception ignored) {}
    }

    @Scheduled(fixedRate = 60000)
    public void cleanupExpiredSessions() {
        otpCache.entrySet().removeIf(entry -> entry.getValue().isExpired());
        resetTokenCache.entrySet().removeIf(entry -> entry.getValue().isExpired());
    }

    @PreDestroy
    public void persistStateOnShutdown() {
        try {
            cleanupExpiredSessions();
            if (otpCache.isEmpty() && resetTokenCache.isEmpty()) {
                Files.deleteIfExists(SNAPSHOT_FILE);
                return;
            }
            try (ObjectOutputStream out = new ObjectOutputStream(Files.newOutputStream(SNAPSHOT_FILE))) {
                out.writeObject(otpCache);
                out.writeObject(resetTokenCache);
                logger.info("Persisted {} active OTPs and {} reset tokens to disk cache.",
                        otpCache.size(), resetTokenCache.size());
            }
        } catch (Exception e) {
            logger.warn("Could not save in-memory OTP cache snapshot: {}", e.getMessage());
        }
    }

    @PostConstruct
    @SuppressWarnings("unchecked")
    public void restoreStateOnStartup() {
        if (!Files.exists(SNAPSHOT_FILE)) return;
        try (ObjectInputStream in = new ObjectInputStream(Files.newInputStream(SNAPSHOT_FILE))) {
            // JEP 290 strict allowlist filter to prevent any remote code execution / gadget chain deserialization attacks
            in.setObjectInputFilter(ObjectInputFilter.Config.createFilter(
                    "java.util.concurrent.**;" +
                    "java.util.**;" +
                    "java.time.**;" +
                    "java.lang.**;" +
                    "com.example.stocksense.**;" +
                    "!*"
            ));
            ConcurrentHashMap<String, OtpSession> loadedOtps = (ConcurrentHashMap<String, OtpSession>) in.readObject();
            ConcurrentHashMap<String, ResetSession> loadedTokens = (ConcurrentHashMap<String, ResetSession>) in.readObject();

            loadedOtps.forEach((k, v) -> { if (!v.isExpired()) otpCache.put(k, v); });
            loadedTokens.forEach((k, v) -> { if (!v.isExpired()) resetTokenCache.put(k, v); });

            logger.info("Restored {} active OTPs and {} reset tokens across service restart.",
                    otpCache.size(), resetTokenCache.size());
        } catch (Exception e) {
            logger.warn("Could not restore in-memory OTP cache: {}", e.getMessage());
        } finally {
            try { Files.deleteIfExists(SNAPSHOT_FILE); } catch (IOException ignored) {}
        }
    }
}

/**
 * OTP Verification and Password Reset Service.
 */
@Service
class OtpService {

    private static final Logger logger = LoggerFactory.getLogger(OtpService.class);
    private static final SecureRandom secureRandom = new SecureRandom();

    private final UserRepository userRepository;
    private final InMemoryOtpStore otpStore;
    private final PasswordEncoder passwordEncoder;
    private final RateLimiter rateLimiter;
    private final AuthService authService;
    private final ObjectProvider<JavaMailSender> mailSenderProvider;
    private final int otpValidityMinutes;
    private final int maxOtpAttempts;
    private final int resendCooldownSeconds;
    private final String mailHost;
    private final String mailFrom;
    private final String mailFromName;

    public OtpService(
            UserRepository userRepository,
            InMemoryOtpStore otpStore,
            PasswordEncoder passwordEncoder,
            RateLimiter rateLimiter,
            AuthService authService,
            ObjectProvider<JavaMailSender> mailSenderProvider,
            @Value("${app.otp.validity-minutes:5}") int otpValidityMinutes,
            @Value("${app.otp.max-attempts:3}") int maxOtpAttempts,
            @Value("${app.otp.resend-cooldown-seconds:60}") int resendCooldownSeconds,
            @Value("${spring.mail.host:}") String mailHost,
            @Value("${app.mail.from:noreply@stocksense.com}") String mailFrom,
            @Value("${app.mail.from-name:StockSense Security}") String mailFromName) {
        this.userRepository = userRepository;
        this.otpStore = otpStore;
        this.passwordEncoder = passwordEncoder;
        this.rateLimiter = rateLimiter;
        this.authService = authService;
        this.mailSenderProvider = mailSenderProvider;
        this.otpValidityMinutes = otpValidityMinutes;
        this.maxOtpAttempts = maxOtpAttempts;
        this.resendCooldownSeconds = resendCooldownSeconds;
        this.mailHost = mailHost;
        this.mailFrom = mailFrom;
        this.mailFromName = mailFromName;
    }

    public void generateAndSendOtp(String email, HttpServletRequest request) {
        String clientIp = authService.extractClientIp(request);
        if (!rateLimiter.isAllowed("otp_" + clientIp)) {
            throw new IllegalStateException("Too many OTP requests from your IP. Please try again later.");
        }

        String cleanEmail = email.trim().toLowerCase();
        Optional<User> userOpt = userRepository.findByEmail(cleanEmail);
        if (userOpt.isEmpty()) {
            // Mitigate User Enumeration: Return silently without error so attacker cannot determine valid emails
            logger.info("[AUDIT] OTP_REQUEST_IGNORED | Email not registered: {} | Client IP: {}", maskEmail(cleanEmail), clientIp);
            return;
        }

        User user = userOpt.get();

        Long secondsSinceLast = otpStore.getSecondsSinceLastOtp(user.getEmail());
        if (secondsSinceLast != null && secondsSinceLast < resendCooldownSeconds) {
            long waitTime = resendCooldownSeconds - secondsSinceLast;
            throw new IllegalStateException("Please wait " + waitTime + " seconds before requesting a new OTP.");
        }

        int otpNumber = 100000 + secureRandom.nextInt(900000);
        String rawOtp = String.valueOf(otpNumber);
        String otpHash = hashOtp(rawOtp);
        Instant expiryDate = Instant.now().plus(Duration.ofMinutes(otpValidityMinutes));

        otpStore.saveOtp(user.getEmail(), otpHash, expiryDate);

        // Dispatch via real SMTP email provider without ever logging the raw OTP to console/logs
        dispatchOtpEmail(user, rawOtp, clientIp);
    }

    private void dispatchOtpEmail(User user, String rawOtp, String clientIp) {
        JavaMailSender mailSender = mailSenderProvider.getIfAvailable();
        if (mailSender == null || mailHost == null || mailHost.isBlank()) {
            logger.info("[AUDIT] OTP generated for recipient: {} (SMTP provider unconfigured) | Client IP: {}",
                    maskEmail(user.getEmail()), clientIp);
            return;
        }

        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setTo(user.getEmail());
            helper.setFrom(mailFrom, mailFromName);
            helper.setSubject("StockSense - Password Reset Verification Code");

            String html = """
                <!DOCTYPE html>
                <html>
                <head>
                  <meta charset="utf-8">
                  <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }
                    .card { max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 32px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
                    .logo { font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 20px; }
                    .logo span { color: #2563eb; }
                    .otp-box { background: #f1f5f9; border-radius: 8px; padding: 20px; text-align: center; margin: 24px 0; border: 1px dashed #cbd5e1; }
                    .otp-code { font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #0f172a; font-family: monospace; }
                    .footer { margin-top: 32px; font-size: 13px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 16px; }
                  </style>
                </head>
                <body>
                  <div class="card">
                    <div class="logo">Stock<span>Sense</span></div>
                    <p>Hello <strong>%s</strong>,</p>
                    <p>We received a request to reset your password for your StockSense account. Use the verification code below to proceed:</p>
                    <div class="otp-box">
                      <div class="otp-code">%s</div>
                    </div>
                    <p>This verification code is valid for <strong>%d minutes</strong>. If you did not request this, you can safely ignore this email.</p>
                    <div class="footer">
                      StockSense Intelligent Inventory Management System<br>
                      Automated Security Dispatch &bull; Do not reply
                    </div>
                  </div>
                </body>
                </html>
                """.formatted(user.getFullName(), rawOtp, otpValidityMinutes);

            String text = "Hello " + user.getFullName() + ",\n\n"
                    + "Your StockSense password reset verification code is: " + rawOtp + "\n\n"
                    + "This code is valid for " + otpValidityMinutes + " minutes.\n"
                    + "If you did not request this, please disregard this email.";

            helper.setText(text, html);
            mailSender.send(message);

            logger.info("[AUDIT] OTP email successfully sent to: {} | Client IP: {}", maskEmail(user.getEmail()), clientIp);
        } catch (Exception e) {
            logger.error("[MAIL_ERROR] Failed to send OTP email to {}: {}", maskEmail(user.getEmail()), e.getMessage());
            throw new RuntimeException("Could not send verification email. Please check SMTP provider configuration.", e);
        }
    }

    private String maskEmail(String email) {
        if (email == null || !email.contains("@")) return "***";
        String[] parts = email.split("@", 2);
        String name = parts[0];
        String domain = parts[1];
        if (name.length() <= 2) {
            return name.charAt(0) + "***@" + domain;
        }
        return name.charAt(0) + "***" + name.charAt(name.length() - 1) + "@" + domain;
    }

    public String verifyOtp(String email, String rawOtp) {
        String cleanEmail = email.trim().toLowerCase();
        User user = userRepository.findByEmail(cleanEmail)
                .orElseThrow(() -> new IllegalArgumentException("Invalid email or OTP request."));

        InMemoryOtpStore.OtpSession session = otpStore.getOtp(cleanEmail);
        if (session == null || session.isExpired()) {
            throw new IllegalArgumentException("OTP has expired or is invalid. Please request a new code.");
        }

        if (session.getAttempts() >= maxOtpAttempts) {
            otpStore.removeOtp(cleanEmail);
            throw new IllegalArgumentException("Maximum verification attempts exceeded. Please request a new OTP.");
        }

        session.incrementAttempts();

        String inputHash = hashOtp(rawOtp.trim());
        boolean matches = MessageDigest.isEqual(
                inputHash.getBytes(StandardCharsets.UTF_8),
                session.getOtpHash().getBytes(StandardCharsets.UTF_8)
        );

        if (!matches) {
            int remaining = maxOtpAttempts - session.getAttempts();
            if (remaining > 0) {
                throw new IllegalArgumentException("Invalid OTP. " + remaining + " attempt(s) remaining.");
            } else {
                otpStore.removeOtp(cleanEmail);
                throw new IllegalArgumentException("Maximum attempts exceeded. This OTP is now invalid. Please request a new one.");
            }
        }

        otpStore.removeOtp(cleanEmail);

        String resetToken = UUID.randomUUID().toString().replace("-", "") +
                Long.toHexString(secureRandom.nextLong());
        Instant resetTokenExpiry = Instant.now().plus(Duration.ofMinutes(5));

        otpStore.saveResetToken(resetToken, user.getId(), cleanEmail, resetTokenExpiry);
        return resetToken;
    }

    @Transactional
    public void resetPassword(String email, String resetToken, String newPassword, HttpServletRequest request) {
        String cleanEmail = email.trim().toLowerCase();
        User user = userRepository.findByEmail(cleanEmail)
                .orElseThrow(() -> new IllegalArgumentException("User not found."));

        InMemoryOtpStore.ResetSession resetSession = otpStore.getResetSession(resetToken);
        if (resetSession == null || resetSession.isExpired()) {
            throw new IllegalArgumentException("Password reset authorization has expired or is invalid. Please request a new OTP.");
        }

        if (!resetSession.getUserId().equals(user.getId()) || !resetSession.getEmail().equalsIgnoreCase(cleanEmail)) {
            throw new IllegalArgumentException("Reset authorization does not match this user account.");
        }

        otpStore.removeResetToken(resetToken);

        user.setPassword(passwordEncoder.encode(newPassword));
        user.setAccountNonLocked(true);
        user.setFailedLoginAttempts(0);
        user.setLockTime(null);
        userRepository.save(user);

        logger.info("[AUDIT] PASSWORD_RESET | Principal: {} | Status: SUCCESS", user.getUsername());
    }

    private String hashOtp(String rawOtp) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(rawOtp.getBytes(StandardCharsets.UTF_8));
            HexFormat hex = HexFormat.of();
            return hex.formatHex(hash);
        } catch (Exception e) {
            throw new RuntimeException("Error hashing OTP", e);
        }
    }
}
