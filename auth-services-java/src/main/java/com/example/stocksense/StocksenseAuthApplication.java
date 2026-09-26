package com.example.stocksense;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class StocksenseAuthApplication {

    public static void main(String[] args) {
        SpringApplication.run(StocksenseAuthApplication.class, args);
    }
}
