package com.drivingassistant.controller;

import com.drivingassistant.exceptions.SessionExpiredException;
import com.drivingassistant.dto.ErrorResponse;
import jakarta.validation.ConstraintViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

import java.time.Instant;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException ex) {
        var fieldErrors = ex.getBindingResult().getFieldErrors().stream()
                .map(err -> new ErrorResponse.FieldError(
                        err.getField(),
                        err.getRejectedValue(),
                        err.getDefaultMessage()
                ))
                .collect(Collectors.toList());

        var error = new ErrorResponse(
                "VALIDATION_ERROR",
                "Ошибка валидации запроса",
                fieldErrors.isEmpty() ? null : fieldErrors.get(0).field(),
                Instant.now(),
                fieldErrors.isEmpty() ? Collections.emptyList() : fieldErrors
        );
        return ResponseEntity.badRequest().body(error);
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ErrorResponse> handleConstraintViolation(ConstraintViolationException ex) {
        var error = new ErrorResponse(
                "VALIDATION_ERROR",
                "Ошибка валидации запроса",
                ex.getConstraintViolations().stream()
                        .findFirst()
                        .map(v -> v.getPropertyPath().toString())
                        .orElse(null),
                Instant.now(),
                Collections.emptyList()
        );
        return ResponseEntity.badRequest().body(error);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGeneric(Exception ex) {
        var error = new ErrorResponse(
                "INTERNAL_ERROR",
                "Внутренняя ошибка сервера",
                null,
                Instant.now(),
                Collections.emptyList()
        );
        return ResponseEntity.internalServerError().body(error);
    }

    @ExceptionHandler(SessionExpiredException.class)
    public ResponseEntity<ErrorResponse> handleSessionExpired(SessionExpiredException ex) {
        var error = new ErrorResponse(
                "SESSION_EXPIRED",
                ex.getMessage(),
                "sessionId",
                Instant.now(),
                List.of()
        );
        return ResponseEntity.status(HttpStatus.GONE).body(error);
    }
}
