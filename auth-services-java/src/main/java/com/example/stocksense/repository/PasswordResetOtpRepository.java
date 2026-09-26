package com.example.stocksense.repository;

import com.example.stocksense.entity.PasswordResetOtp;
import com.example.stocksense.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface PasswordResetOtpRepository extends JpaRepository<PasswordResetOtp, Long> {
    Optional<PasswordResetOtp> findTopByUserOrderByCreatedAtDesc(User user);
    Optional<PasswordResetOtp> findByResetToken(String resetToken);
    void deleteByUser(User user);
}
