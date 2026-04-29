package com.sharks.auth.internal;

import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClientResponseException;

import com.sharks.auth.service.AuthService;
import com.sharks.auth.web.dto.LoginRequest;
import com.sharks.auth.web.dto.SignupRequest;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/internal/auth")
public class InternalAuthController {

	private final AuthService authService;

	public InternalAuthController(AuthService authService) {
		this.authService = authService;
	}

	@PostMapping("/login")
	public ResponseEntity<?> login(@Valid @RequestBody LoginRequest body) {
		try {
			Map<String, Object> tokenResponse = authService.login(body.getEmail(), body.getPassword());
			return ResponseEntity.ok(tokenResponse);
		} catch (RestClientResponseException e) {
			return ResponseEntity.status(e.getStatusCode()).body(e.getResponseBodyAsString());
		} catch (IllegalStateException e) {
			return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(Map.of("error", e.getMessage()));
		} catch (IllegalArgumentException e) {
			return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
		}
	}

	@PostMapping("/signup")
	public ResponseEntity<?> signup(@Valid @RequestBody SignupRequest body) {
		try {
			Map<String, Object> responseBody = authService.signup(body.getEmail(), body.getPassword());
			return ResponseEntity.status(HttpStatus.CREATED).body(responseBody);
		} catch (RestClientResponseException e) {
			int code = e.getStatusCode().value();
			if (code == 422 || code == 409) {
				return ResponseEntity.status(HttpStatus.CONFLICT).body(e.getResponseBodyAsString());
			}
			return ResponseEntity.status(e.getStatusCode()).body(e.getResponseBodyAsString());
		} catch (IllegalStateException e) {
			return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(Map.of("error", e.getMessage()));
		} catch (IllegalArgumentException e) {
			return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
		}
	}
}
