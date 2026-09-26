package com.example.stocksense.security;

import com.example.stocksense.entity.User;
import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

@Service
public class JwtService {

    private static final Logger logger = LoggerFactory.getLogger(JwtService.class);
    private static final String HMAC_SHA256 = "HmacSHA256";
    private static final String JWT_HEADER_BASE64 = Base64.getUrlEncoder().withoutPadding()
            .encodeToString("{\"alg\":\"HS256\",\"typ\":\"JWT\"}".getBytes(StandardCharsets.UTF_8));

    private final ObjectMapper objectMapper;
    private final String secretKey;
    private final long accessTokenExpirationSeconds;
    private final String issuer;

    public JwtService(
            ObjectMapper objectMapper,
            @Value("${app.jwt.secret:StockSenseProductionSecureSecretKeyMinimum256BitsLongForHmacSha256!}") String secretKey,
            @Value("${app.jwt.access-token-expiration-seconds:900}") long accessTokenExpirationSeconds,
            @Value("${app.jwt.issuer:stocksense-auth-service}") String issuer) {
        this.objectMapper = objectMapper;
        this.secretKey = secretKey;
        this.accessTokenExpirationSeconds = accessTokenExpirationSeconds;
        this.issuer = issuer;
    }

    public String generateAccessToken(User user) {
        Instant now = Instant.now();
        Instant expiry = now.plusSeconds(accessTokenExpirationSeconds);

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

            String dataToSign = JWT_HEADER_BASE64 + "." + encodedPayload;
            String signature = sign(dataToSign, secretKey);

            return dataToSign + "." + signature;
        } catch (Exception e) {
            logger.error("Failed to generate JWT access token", e);
            throw new RuntimeException("Could not create JWT token", e);
        }
    }

    public boolean validateToken(String token) {
        if (token == null || token.isBlank()) {
            return false;
        }

        String[] parts = token.split("\\.");
        if (parts.length != 3) {
            return false;
        }

        try {
            String dataToSign = parts[0] + "." + parts[1];
            String expectedSignature = sign(dataToSign, secretKey);

            // Constant-time comparison to prevent timing attacks
            if (!MessageDigest.isEqual(parts[2].getBytes(StandardCharsets.UTF_8), expectedSignature.getBytes(StandardCharsets.UTF_8))) {
                logger.warn("JWT signature validation failed");
                return false;
            }

            Map<String, Object> claims = parsePayload(parts[1]);
            if (claims == null) {
                return false;
            }

            // Expiration check
            Object expObj = claims.get("exp");
            if (expObj instanceof Number expNumber) {
                long exp = expNumber.longValue();
                if (Instant.now().getEpochSecond() > (exp + 30)) { // 30s clock skew tolerance
                    logger.debug("JWT token has expired");
                    return false;
                }
            } else {
                return false;
            }

            return true;
        } catch (Exception e) {
            logger.warn("JWT validation exception: {}", e.getMessage());
            return false;
        }
    }

    public Map<String, Object> getClaims(String token) {
        if (token == null) {
            return null;
        }
        String[] parts = token.split("\\.");
        if (parts.length != 3) {
            return null;
        }
        return parsePayload(parts[1]);
    }

    public Long getUserIdFromToken(String token) {
        Map<String, Object> claims = getClaims(token);
        if (claims != null && claims.containsKey("sub")) {
            return Long.valueOf(claims.get("sub").toString());
        }
        return null;
    }

    public String getUsernameFromToken(String token) {
        Map<String, Object> claims = getClaims(token);
        if (claims != null && claims.containsKey("username")) {
            return claims.get("username").toString();
        }
        return null;
    }

    public String getEmailFromToken(String token) {
        Map<String, Object> claims = getClaims(token);
        if (claims != null && claims.containsKey("email")) {
            return claims.get("email").toString();
        }
        return null;
    }

    public long getAccessTokenExpirationSeconds() {
        return accessTokenExpirationSeconds;
    }

    public String getSecretKey() {
        return secretKey;
    }

    public String getIssuer() {
        return issuer;
    }

    private String sign(String data, String secret) throws Exception {
        Mac mac = Mac.getInstance(HMAC_SHA256);
        SecretKeySpec secretKeySpec = new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), HMAC_SHA256);
        mac.init(secretKeySpec);
        byte[] rawHmac = mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
        return Base64.getUrlEncoder().withoutPadding().encodeToString(rawHmac);
    }

    private Map<String, Object> parsePayload(String base64Payload) {
        try {
            byte[] decoded = Base64.getUrlDecoder().decode(base64Payload);
            String json = new String(decoded, StandardCharsets.UTF_8);
            return objectMapper.readValue(json, new TypeReference<HashMap<String, Object>>() {});
        } catch (Exception e) {
            logger.error("Failed to parse JWT payload", e);
            return null;
        }
    }
}
