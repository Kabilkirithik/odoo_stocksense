package com.example.stocksense;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.mock.web.MockHttpServletRequest;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
class AuthControllerTests {

    @Autowired
    private AuthService authService;

    @Autowired
    private OtpService otpService;

    @Autowired
    private InMemoryOtpStore otpStore;

    @Autowired
    private JwtTokenService jwtService;

    @Autowired
    private UserRepository userRepository;

    @BeforeEach
    void setUp() {
        userRepository.deleteAll();
        otpStore.clear();
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
        assertNotNull(regResponse.getToken());
        assertEquals("manager@stocksense.com", regResponse.getUser().getEmail());

        // 2. Validate JWT token
        assertTrue(jwtService.validateToken(regResponse.getToken()));
        assertEquals("stockmanager", jwtService.getUsernameFromToken(regResponse.getToken()));

        // 3. Login
        LoginRequest loginReq = new LoginRequest("stockmanager", "P@ssword123!");
        var loginResponse = authService.login(loginReq, request);
        assertNotNull(loginResponse.getToken());
        assertEquals("manager@stocksense.com", loginResponse.getUser().getEmail());

        // 4. Validate Token for Python Backend
        var validation = authService.validateTokenForBackend(loginResponse.getToken());
        assertTrue(validation.isValid());
        assertEquals("stockmanager", validation.getUsername());
        assertEquals("manager@stocksense.com", validation.getEmail());
    }

    @Test
    void testInMemoryOtpPasswordResetFlow() {
        MockHttpServletRequest request = new MockHttpServletRequest();

        // Register user
        RegisterRequest registerReq = new RegisterRequest(
                "staffuser",
                "staff@stocksense.com",
                "OldP@ssword123!",
                "Warehouse Staff"
        );
        authService.register(registerReq, request);

        // Request OTP (stored in memory)
        otpService.generateAndSendOtp("staff@stocksense.com", request);

        // In-memory OTP session exists
        var session = otpStore.getOtp("staff@stocksense.com");
        assertNotNull(session);
        assertNotNull(session.getOtpHash());
        assertFalse(session.isExpired());

        // Cooldown protection test: consecutive request within cooldown throws IllegalStateException
        assertThrows(IllegalStateException.class, () -> {
            otpService.generateAndSendOtp("staff@stocksense.com", request);
        });

        // Verification with invalid OTP fails
        assertThrows(IllegalArgumentException.class, () -> {
            otpService.verifyOtp("staff@stocksense.com", "000000");
        });
    }

    @Test
    void testRestartSnapshotSurvivability() {
        // Populate cache
        otpStore.saveOtp("test@stocksense.com", "dummy_hash", java.time.Instant.now().plusSeconds(300));
        assertNotNull(otpStore.getOtp("test@stocksense.com"));

        // Trigger shutdown persistence
        otpStore.persistStateOnShutdown();

        // Clear in-memory state
        otpStore.removeOtp("test@stocksense.com");
        assertNull(otpStore.getOtp("test@stocksense.com"));

        // Trigger startup restoration
        otpStore.restoreStateOnStartup();

        // Verify active OTP survived!
        assertNotNull(otpStore.getOtp("test@stocksense.com"));
    }
}
