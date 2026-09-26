package com.example.stocksense.security;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedQueue;

@Service
public class RateLimiterService {

    private final int maxRequestsPerWindow;
    private final long windowDurationMillis;
    private final ConcurrentHashMap<String, ConcurrentLinkedQueue<Long>> requestTracker = new ConcurrentHashMap<>();

    public RateLimiterService(
            @Value("${app.security.rate-limit.max-requests:20}") int maxRequestsPerWindow,
            @Value("${app.security.rate-limit.window-seconds:60}") long windowSeconds) {
        this.maxRequestsPerWindow = maxRequestsPerWindow;
        this.windowDurationMillis = windowSeconds * 1000L;
    }

    public boolean isAllowed(String key) {
        long now = Instant.now().toEpochMilli();
        long windowStart = now - windowDurationMillis;

        ConcurrentLinkedQueue<Long> timestamps = requestTracker.computeIfAbsent(key, k -> new ConcurrentLinkedQueue<>());

        // Evict expired timestamps
        while (!timestamps.isEmpty() && timestamps.peek() < windowStart) {
            timestamps.poll();
        }

        if (timestamps.size() >= maxRequestsPerWindow) {
            return false;
        }

        timestamps.add(now);
        return true;
    }

    public void reset(String key) {
        requestTracker.remove(key);
    }
}
