package com.example.stocksense.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class EmailService {

    private static final Logger logger = LoggerFactory.getLogger(EmailService.class);

    public void sendOtpEmail(String recipientEmail, String recipientName, String otp, int validityMinutes) {
        // High visibility developer / production log banner
        logger.info("\n" +
                "========================================================================\n" +
                "               [STOCKSENSE AUTH] PASSWORD RESET OTP                     \n" +
                "========================================================================\n" +
                " To:          {} ({})\n" +
                " OTP Code:    {}\n" +
                " Validity:    {} minutes\n" +
                " Notice:      Do not share this OTP with anyone.\n" +
                "========================================================================",
                recipientEmail, recipientName != null ? recipientName : "User", otp, validityMinutes);

        // Production note: When configuring real SMTP (JavaMailSender / SendGrid / AWS SES),
        // plug in the mail sender logic here.
    }
}
