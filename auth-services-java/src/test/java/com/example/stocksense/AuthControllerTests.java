package com.example.stocksense;

import com.example.stocksense.dto.LoginRequest;
import com.example.stocksense.dto.RegisterRequest;
import com.example.stocksense.entity.PasswordResetOtp;
import com.example.stocksense.entity.User;
import com.example.stocksense.repository.PasswordResetOtpRepository;
import com.example.stocksense.repository.UserRepository;
import com.example.stocksense.security.JwtService;
import com.example.stocksense.service.AuthService;
import com.example.stocksense.service.OtpService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.mock.web.MockHttpServletRequest;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
class AuthControllerTests {

    @Autowired
    private AuthService authService;

    @Autowired
    private OtpService otpService;

    @Autowired
    private JwtService jwtService;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordResetOtpRepository otpRepository;

    @Autowired
    private com.example.stocksense.repository.RefreshTokenRepository refreshTokenRepository;

    @BeforeEach
    void setUp() {
        otpRepository.deleteAll();
        refreshTokenRepository.deleteAll();
        userRepository.deleteAll();
    }

    @Test
    void testRegistrationAndLoginFlow() {
        MockHttpServletRequest request = new MockHttpServletRequest();

        // 1. Register
        RegisterRequest registerReq = new RegisterRequest(
                "stockmanager",
                "manager@stocksense.com",
                "P@ssword123!",
                "Inventory Manager"
        );

        var regResponse = authService.register(registerReq, request);
        assertNotNull(regResponse.getAccessToken());
        assertNotNull(regResponse.getRefreshToken());
        assertEquals("manager@stocksense.com", regResponse.getUser().getEmail());

        // 2. Validate JWT token
        assertTrue(jwtService.validateToken(regResponse.getAccessToken()));
        assertEquals("stockmanager", jwtService.getUsernameFromToken(regResponse.getAccessToken()));

        // 3. Login
        LoginRequest loginReq = new LoginRequest("stockmanager", "P@ssword123!");
        var loginResponse = authService.login(loginReq, request);
        assertNotNull(loginResponse.getAccessToken());
        assertEquals("manager@stocksense.com", loginResponse.getUser().getEmail());

        // 4. Validate Token for Python Backend
        var validation = authService.validateTokenForBackend(loginResponse.getAccessToken());
        assertTrue(validation.isValid());
        assertEquals("stockmanager", validation.getUsername());
        assertEquals("manager@stocksense.com", validation.getEmail());
    }

    @Test
    void testOtpPasswordResetFlow() {
        MockHttpServletRequest request = new MockHttpServletRequest();

        // Register user
        RegisterRequest registerReq = new RegisterRequest(
                "staffuser",
                "staff@stocksense.com",
                "OldP@ssword123!",
                "Warehouse Staff"
        );
        authService.register(registerReq, request);

        // Request OTP
        otpService.generateAndSendOtp("staff@stocksense.com", request);

        User user = userRepository.findByEmail("staff@stocksense.com").orElseThrow();
        PasswordResetOtp otp = otpRepository.findTopByUserOrderByCreatedAtDesc(user).orElseThrow();
        assertNotNull(otp.getOtpHash());
        assertFalse(otp.isExpired());

        // Verify with invalid OTP first
        assertThrows(IllegalArgumentException.class, () -> {
            otpService.verifyOtp("staff@stocksense.com", "000000");
        });
    }
}
