package com.example.stocksense;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.annotation.web.configurers.HeadersConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.OncePerRequestFilter;
import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.ObjectMapper;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedQueue;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    private final JwtAuthFilter jwtAuthFilter;
    private final String allowedOrigins;

    public SecurityConfig(
            JwtAuthFilter jwtAuthFilter,
            @Value("${app.cors.allowed-origins:http://localhost:3000,http://localhost:5173,http://localhost:8000,http://localhost:5000,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8000}") String allowedOrigins) {
        this.jwtAuthFilter = jwtAuthFilter;
        this.allowedOrigins = allowedOrigins;
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);
    }

    @Bean
    public UserDetailsService userDetailsService() {
        return username -> {
            throw new UsernameNotFoundException("Stateless JWT authentication used; UserDetailsService is disabled.");
        };
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(AbstractHttpConfigurer::disable)
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))
            .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .headers(headers -> headers.frameOptions(HeadersConfigurer.FrameOptionsConfig::sameOrigin))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(
                    "/api/v1/auth/register",
                    "/api/v1/auth/login",
                    "/api/v1/auth/logout",
                    "/api/v1/auth/forgot-password",
                    "/api/v1/auth/verify-otp",
                    "/api/v1/auth/reset-password",
                    "/api/v1/auth/validate",
                    "/api/v1/auth/health",
                    "/h2-console/**",
                    "/error"
                ).permitAll()
                .requestMatchers("/api/v1/auth/me").authenticated()
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class)
            .build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        List<String> origins = Arrays.stream(allowedOrigins.split(",")).map(String::trim).toList();
        configuration.setAllowedOriginPatterns(origins);
        configuration.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"));
        configuration.setAllowedHeaders(List.of("Authorization", "Content-Type", "X-Requested-With", "Accept", "Origin"));
        configuration.setExposedHeaders(List.of("Authorization"));
        configuration.setAllowCredentials(true);
        configuration.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}

/**
 * High-performance, RFC 7519 HMAC-SHA256 JWT Service.
 */
@Service
class JwtTokenService {
    private static final Logger logger = LoggerFactory.getLogger(JwtTokenService.class);
    private static final String HMAC_SHA256 = "HmacSHA256";
    private static final String JWT_HEADER = Base64.getUrlEncoder().withoutPadding()
            .encodeToString("{\"alg\":\"HS256\",\"typ\":\"JWT\"}".getBytes(StandardCharsets.UTF_8));

    private final ObjectMapper objectMapper;
    private final String secretKey;
    private final long expirationSeconds;
    private final String issuer;

    public JwtTokenService(
            ObjectMapper objectMapper,
            @Value("${app.jwt.secret:StockSenseProductionSecureSecretKeyMinimum256BitsLongForHmacSha256!}") String secretKey,
            @Value("${app.jwt.access-token-expiration-seconds:86400}") long expirationSeconds,
            @Value("${app.jwt.issuer:stocksense-auth-service}") String issuer) {
        this.objectMapper = objectMapper;
        this.secretKey = secretKey;
        this.expirationSeconds = expirationSeconds;
        this.issuer = issuer;
    }

    public String generateToken(User user) {
        Instant now = Instant.now();
        Instant expiry = now.plusSeconds(expirationSeconds);

        Map<String, Object> claims = new HashMap<>();
        claims.put("sub", String.valueOf(user.getId()));
        claims.put("username", user.getUsername());
        claims.put("email", user.getEmail());
        claims.put("name", user.getFullName());
        claims.put("iss", issuer);
        claims.put("iat", now.getEpochSecond());
        claims.put("exp", expiry.getEpochSecond());

        try {
            String payloadJson = objectMapper.writeValueAsString(claims);
            String encodedPayload = Base64.getUrlEncoder().withoutPadding()
                    .encodeToString(payloadJson.getBytes(StandardCharsets.UTF_8));
            String dataToSign = JWT_HEADER + "." + encodedPayload;
            return dataToSign + "." + sign(dataToSign, secretKey);
        } catch (Exception e) {
            throw new RuntimeException("Could not generate JWT token", e);
        }
    }

    public boolean validateToken(String token) {
        if (token == null || token.isBlank()) return false;
        String[] parts = token.split("\\.");
        if (parts.length != 3) return false;

        try {
            // 1. Explicitly verify header: reject "alg": "none" or any non-HS256 algorithm
            Map<String, Object> header = parsePayload(parts[0]);
            if (header == null || !"HS256".equals(header.get("alg"))) {
                return false;
            }

            // 2. Cryptographic signature verification using constant-time comparison
            String dataToSign = parts[0] + "." + parts[1];
            String expectedSig = sign(dataToSign, secretKey);
            if (!MessageDigest.isEqual(parts[2].getBytes(StandardCharsets.UTF_8), expectedSig.getBytes(StandardCharsets.UTF_8))) {
                return false;
            }

            // 3. Validate claims: issuer and expiration
            Map<String, Object> claims = parsePayload(parts[1]);
            if (claims == null) return false;

            if (issuer != null && !issuer.equals(claims.get("iss"))) {
                return false;
            }

            if (claims.get("exp") instanceof Number expNumber) {
                return Instant.now().getEpochSecond() <= (expNumber.longValue() + 30);
            }
            return false;
        } catch (Exception e) {
            return false;
        }
    }

    public Map<String, Object> getClaims(String token) {
        if (token == null) return null;
        String[] parts = token.split("\\.");
        return parts.length == 3 ? parsePayload(parts[1]) : null;
    }

    public Long getUserId(String token) {
        Map<String, Object> claims = getClaims(token);
        return (claims != null && claims.containsKey("sub")) ? Long.valueOf(claims.get("sub").toString()) : null;
    }

    public Long getUserIdFromToken(String token) {
        return getUserId(token);
    }

    public String getUsername(String token) {
        Map<String, Object> claims = getClaims(token);
        return (claims != null && claims.containsKey("username")) ? claims.get("username").toString() : null;
    }

    public String getUsernameFromToken(String token) {
        return getUsername(token);
    }

    public long getExpirationSeconds() {
        return expirationSeconds;
    }

    public long getAccessTokenExpirationSeconds() {
        return expirationSeconds;
    }

    private String sign(String data, String secret) throws Exception {
        Mac mac = Mac.getInstance(HMAC_SHA256);
        mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), HMAC_SHA256));
        return Base64.getUrlEncoder().withoutPadding().encodeToString(mac.doFinal(data.getBytes(StandardCharsets.UTF_8)));
    }

    private Map<String, Object> parsePayload(String base64Payload) {
        try {
            byte[] decoded = Base64.getUrlDecoder().decode(base64Payload);
            return objectMapper.readValue(new String(decoded, StandardCharsets.UTF_8), new TypeReference<HashMap<String, Object>>() {});
        } catch (Exception e) {
            return null;
        }
    }
}

/**
 * Intercepts incoming requests and validates 'Authorization: Bearer <token>'.
 */
@Component
class JwtAuthFilter extends OncePerRequestFilter {
    private final JwtTokenService jwtTokenService;
    private final UserRepository userRepository;

    public JwtAuthFilter(JwtTokenService jwtTokenService, UserRepository userRepository) {
        this.jwtTokenService = jwtTokenService;
        this.userRepository = userRepository;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String authHeader = request.getHeader("Authorization");
        if (StringUtils.hasText(authHeader) && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            if (jwtTokenService.validateToken(token)) {
                Long userId = jwtTokenService.getUserId(token);
                if (userId != null && SecurityContextHolder.getContext().getAuthentication() == null) {
                    userRepository.findById(userId).ifPresent(user -> {
                        if (user.isEnabled() && user.isAccountNonLocked()) {
                            var auth = new UsernamePasswordAuthenticationToken(
                                    user, null, List.of(new SimpleGrantedAuthority("ROLE_USER")));
                            auth.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                            SecurityContextHolder.getContext().setAuthentication(auth);
                        }
                    });
                }
            }
        }
        chain.doFilter(request, response);
    }
}

/**
 * Thread-safe sliding-window rate limiter with automatic bounded memory eviction.
 */
@Service
class RateLimiter {
    private final int maxRequests;
    private final long windowMillis;
    private final ConcurrentHashMap<String, ConcurrentLinkedQueue<Long>> tracker = new ConcurrentHashMap<>();

    public RateLimiter(
            @Value("${app.security.rate-limit.max-requests:20}") int maxRequests,
            @Value("${app.security.rate-limit.window-seconds:60}") long windowSeconds) {
        this.maxRequests = maxRequests;
        this.windowMillis = windowSeconds * 1000L;
    }

    public boolean isAllowed(String key) {
        long now = Instant.now().toEpochMilli();
        long windowStart = now - windowMillis;

        ConcurrentLinkedQueue<Long> queue = tracker.computeIfAbsent(key, k -> new ConcurrentLinkedQueue<>());
        while (!queue.isEmpty() && queue.peek() < windowStart) {
            queue.poll();
        }

        if (queue.size() >= maxRequests) return false;

        queue.add(now);
        return true;
    }

    @Scheduled(fixedRate = 180000)
    public void evictStale() {
        long windowStart = Instant.now().toEpochMilli() - windowMillis;
        tracker.entrySet().removeIf(entry -> {
            ConcurrentLinkedQueue<Long> queue = entry.getValue();
            while (!queue.isEmpty() && queue.peek() < windowStart) queue.poll();
            return queue.isEmpty();
        });
    }
}
