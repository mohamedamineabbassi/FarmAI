package com.farm.backend.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<Map<String, String>> handleRuntimeException(RuntimeException ex) {
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(Map.of("error", ex.getMessage() != null ? ex.getMessage() : "Erreur serveur"));
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<Map<String, String>> handleAccessDenied(AccessDeniedException ex) {
        return ResponseEntity
                .status(HttpStatus.FORBIDDEN)
                .body(Map.of("error", "Accès refusé : permissions insuffisantes"));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> handleGenericException(Exception ex) {
        ex.printStackTrace();
        return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Erreur interne du serveur : " + ex.getMessage()));
    }
}
