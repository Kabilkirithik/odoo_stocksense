package com.example.stocksense.dto;

public class TokenValidationResponse {

    private boolean valid;
    private Long userId;
    private String username;
    private String email;
    private String fullName;
    private Long expiresAt;
    private String error;

    public TokenValidationResponse() {
    }

    public static TokenValidationResponse valid(Long userId, String username, String email, String fullName, Long expiresAt) {
        TokenValidationResponse response = new TokenValidationResponse();
        response.setValid(true);
        response.setUserId(userId);
        response.setUsername(username);
        response.setEmail(email);
        response.setFullName(fullName);
        response.setExpiresAt(expiresAt);
        return response;
    }

    public static TokenValidationResponse invalid(String error) {
        TokenValidationResponse response = new TokenValidationResponse();
        response.setValid(false);
        response.setError(error);
        return response;
    }

    public boolean isValid() {
        return valid;
    }

    public void setValid(boolean valid) {
        this.valid = valid;
    }

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getFullName() {
        return fullName;
    }

    public void setFullName(String fullName) {
        this.fullName = fullName;
    }

    public Long getExpiresAt() {
        return expiresAt;
    }

    public void setExpiresAt(Long expiresAt) {
        this.expiresAt = expiresAt;
    }

    public String getError() {
        return error;
    }

    public void setError(String error) {
        this.error = error;
    }
}
