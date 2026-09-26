package com.example.stocksense.service;

import com.example.stocksense.entity.PasswordResetOtp;
import com.example.stocksense.entity.User;
import com.example.stocksense.repository.PasswordResetOtpRepository;
import com.example.stocksense.repository.RefreshTokenRepository;
import com.example.stocksense.repository.UserRepository;
import com.example.stocksense.security.SecurityAuditService;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.util.HexFormat;
import java.util.Optional;
import java.util.UUID;

@Service
public class OtpService {

    private static final Logger logger = LoggerFactory.getLogger(OtpService.class);
    private static final SecureRandom secureRandom = new SecureRandom();

    private final UserRepository userRepository;
    private final PasswordResetOtpRepository otpRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final EmailService emailService;
    private final SecurityAuditService auditService;

    private final int otpValidityMinutes;
    private final int maxOtpAttempts;
    private final int resendCooldownSeconds;

    public OtpService(
            UserRepository userRepository,
            PasswordResetOtpRepository otpRepository,
            RefreshTokenRepository refreshTokenRepository,
            PasswordEncoder passwordEncoder,
            EmailService emailService,
            SecurityAuditService auditService,
            @Value("${app.otp.validity-minutes:5}") int otpValidityMinutes,
            @Value("${app.otp.max-attempts:3}") int maxOtpAttempts,
            @Value("${app.otp.resend-cooldown-seconds:60}") int resendCooldownSeconds) {
        this.userRepository = userRepository;
        this.otpRepository = otpRepository;
        this.refreshTokenRepository = refreshTokenRepository;
        this.passwordEncoder = passwordEncoder;
        this.emailService = emailService;
        this.auditService = auditService;
        this.otpValidityMinutes = otpValidityMinutes;
        this.maxOtpAttempts = maxOtpAttempts;
        this.resendCooldownSeconds = resendCooldownSeconds;
    }

    @Transactional
    public void generateAndSendOtp(String email, HttpServletRequest request) {
        User user = userRepository.findByEmail(email.trim().toLowerCase())
                .orElseThrow(() -> new IllegalArgumentException("No account found with this email address."));

        // Check resend cooldown
        Optional<PasswordResetOtp> existingOtp = otpRepository.findTopByUserOrderByCreatedAtDesc(user);
        if (existingOtp.isPresent()) {
            PasswordResetOtp lastOtp = existingOtp.get();
            long secondsSinceLast = Duration.between(lastOtp.getCreatedAt(), Instant.now()).getSeconds();
            if (secondsSinceLast < resendCooldownSeconds && !lastOtp.isUsed()) {
                long waitTime = resendCooldownSeconds - secondsSinceLast;
                throw new IllegalStateException("Please wait " + waitTime + " seconds before requesting a new OTP.");
            }
        }

        // Generate 6-digit numeric OTP (100000 - 999999)
        int otpNumber = 100000 + secureRandom.nextInt(900000);
        String rawOtp = String.valueOf(otpNumber);

        // Hash OTP for secure storage
        String otpHash = hashOtp(rawOtp);
        Instant expiryDate = Instant.now().plus(Duration.ofMinutes(otpValidityMinutes));

        PasswordResetOtp otpEntity = new PasswordResetOtp(user, otpHash, expiryDate);
        otpRepository.save(otpEntity);

        // Send OTP via email service
        emailService.sendOtpEmail(user.getEmail(), user.getFullName(), rawOtp, otpValidityMinutes);

        auditService.recordEvent(user.getUsername(), "OTP_REQUESTED", request, "Password reset OTP requested");
    }

    @Transactional
    public String verifyOtp(String email, String rawOtp) {
        User user = userRepository.findByEmail(email.trim().toLowerCase())
                .orElseThrow(() -> new IllegalArgumentException("Invalid email or OTP request."));

        PasswordResetOtp otpEntity = otpRepository.findTopByUserOrderByCreatedAtDesc(user)
                .orElseThrow(() -> new IllegalArgumentException("No active OTP found. Please request a new one."));

        if (otpEntity.isUsed()) {
            throw new IllegalArgumentException("This OTP has already been used. Please request a new one.");
        }

        if (otpEntity.isExpired()) {
            throw new IllegalArgumentException("OTP has expired. Please request a new code.");
        }

        if (otpEntity.getAttempts() >= maxOtpAttempts) {
            throw new IllegalArgumentException("Maximum verification attempts exceeded. Please request a new OTP.");
        }

        otpEntity.setAttempts(otpEntity.getAttempts() + 1);

        String inputHash = hashOtp(rawOtp.trim());
        boolean matches = MessageDigest.isEqual(
                inputHash.getBytes(StandardCharsets.UTF_8),
                otpEntity.getOtpHash().getBytes(StandardCharsets.UTF_8)
        );

        if (!matches) {
            otpRepository.save(otpEntity);
            int remaining = maxOtpAttempts - otpEntity.getAttempts();
            if (remaining > 0) {
                throw new IllegalArgumentException("Invalid OTP. " + remaining + " attempt(s) remaining.");
            } else {
                throw new IllegalArgumentException("Maximum attempts exceeded. This OTP is now invalid. Please request a new one.");
            }
        }

        // OTP is verified. Generate one-time reset authorization token (valid for 5 minutes)
        String resetToken = UUID.randomUUID().toString().replace("-", "") +
                Long.toHexString(secureRandom.nextLong());
        otpEntity.setVerified(true);
        otpEntity.setResetToken(resetToken);
        otpEntity.setResetTokenExpiry(Instant.now().plus(Duration.ofMinutes(5)));
        otpRepository.save(otpEntity);

        return resetToken;
    }

    @Transactional
    public void resetPassword(String email, String resetToken, String newPassword, HttpServletRequest request) {
        User user = userRepository.findByEmail(email.trim().toLowerCase())
                .orElseThrow(() -> new IllegalArgumentException("User not found."));

        PasswordResetOtp otpEntity = otpRepository.findByResetToken(resetToken)
                .orElseThrow(() -> new IllegalArgumentException("Invalid or expired password reset authorization."));

        if (!otpEntity.getUser().getId().equals(user.getId())) {
            throw new IllegalArgumentException("Reset authorization does not match user account.");
        }

        if (otpEntity.isUsed()) {
            throw new IllegalArgumentException("This reset link/token has already been used.");
        }

        if (otpEntity.isResetTokenExpired()) {
            throw new IllegalArgumentException("Reset token has expired. Please initiate the reset process again.");
        }

        // Update password with BCrypt (12 rounds)
        user.setPassword(passwordEncoder.encode(newPassword));
        user.setAccountNonLocked(true);
        user.setFailedLoginAttempts(0);
        user.setLockTime(null);
        userRepository.save(user);

        // Mark OTP as used
        otpEntity.setUsed(true);
        otpRepository.save(otpEntity);

        // Invalidate all active refresh tokens for this user across all devices!
        refreshTokenRepository.revokeAllByUser(user);

        auditService.recordEvent(user.getUsername(), "PASSWORD_RESET", request, "Password successfully reset via OTP");
    }

    private String hashOtp(String rawOtp) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(rawOtp.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hash);
        } catch (Exception e) {
            throw new RuntimeException("Error hashing OTP", e);
        }
    }
}
