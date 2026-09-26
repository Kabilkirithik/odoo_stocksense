package com.example.stocksense.security;

import com.example.stocksense.entity.AuditLog;
import com.example.stocksense.repository.AuditLogRepository;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class SecurityAuditService {

    private static final Logger logger = LoggerFactory.getLogger(SecurityAuditService.class);
    private final AuditLogRepository auditLogRepository;

    public SecurityAuditService(AuditLogRepository auditLogRepository) {
        this.auditLogRepository = auditLogRepository;
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void recordEvent(String username, String action, HttpServletRequest request, String details) {
        try {
            String ipAddress = extractClientIp(request);
            String userAgent = request != null ? request.getHeader("User-Agent") : "Unknown";
            if (userAgent != null && userAgent.length() > 250) {
                userAgent = userAgent.substring(0, 250);
            }

            AuditLog log = new AuditLog(
                    username != null ? username : "anonymous",
                    action,
                    ipAddress,
                    userAgent,
                    details
            );
            auditLogRepository.save(log);
            logger.info("SECURITY AUDIT: action={}, user={}, ip={}, details={}", action, username, ipAddress, details);
        } catch (Exception e) {
            logger.error("Failed to record security audit log: {}", e.getMessage());
        }
    }

    public String extractClientIp(HttpServletRequest request) {
        if (request == null) {
            return "127.0.0.1";
        }
        String xForwardedFor = request.getHeader("X-Forwarded-For");
        if (xForwardedFor != null && !xForwardedFor.isBlank()) {
            return xForwardedFor.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }
}
