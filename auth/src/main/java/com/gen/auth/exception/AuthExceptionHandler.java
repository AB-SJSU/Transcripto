package com.gen.auth.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class AuthExceptionHandler {

	@ExceptionHandler(SupabaseAuthException.class)
	ResponseEntity<ProblemDetail> handleSupabaseAuth(SupabaseAuthException ex) {
		int code = switch (ex.getStatusCode()) {
			case 400, 401 -> HttpStatus.UNAUTHORIZED.value();
			case 403 -> HttpStatus.FORBIDDEN.value();
			case 404 -> HttpStatus.NOT_FOUND.value();
			case 422 -> HttpStatus.UNPROCESSABLE_ENTITY.value();
			default -> ex.getStatusCode() >= 500 ? HttpStatus.BAD_GATEWAY.value() : HttpStatus.BAD_REQUEST.value();
		};
		HttpStatusCode status = HttpStatusCode.valueOf(code);
		String message = code == HttpStatus.UNAUTHORIZED.value() ? "Invalid email or password" : "Auth request failed";
		ProblemDetail detail = ProblemDetail.forStatusAndDetail(status, message);
		detail.setTitle("Authentication error");
		return ResponseEntity.status(status).body(detail);
	}

	@ExceptionHandler(MethodArgumentNotValidException.class)
	ResponseEntity<ProblemDetail> handleValidation(MethodArgumentNotValidException ex) {
		ProblemDetail detail = ProblemDetail.forStatusAndDetail(
			HttpStatus.BAD_REQUEST,
			"Invalid request body"
		);
		detail.setTitle("Validation error");
		return ResponseEntity.badRequest().body(detail);
	}
}
