package com.sharks.auth.web;

import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClientResponseException;

import com.sharks.auth.client.SupabaseAuthClient;
import com.sharks.auth.web.dto.LoginRequest;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

	private final SupabaseAuthClient supabaseAuthClient;

	public AuthController(SupabaseAuthClient supabaseAuthClient) {
		this.supabaseAuthClient = supabaseAuthClient;
	}

	@PostMapping("/login")
	public ResponseEntity<?> login(@Valid @RequestBody LoginRequest body) {
		try {
			Map<String, Object> tokenResponse = supabaseAuthClient.signInWithPassword(body.getEmail(), body.getPassword());
			return ResponseEntity.ok(tokenResponse);
		} catch (RestClientResponseException e) {
			return ResponseEntity.status(e.getStatusCode()).body(e.getResponseBodyAsString());
		} catch (IllegalStateException e) {
			return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(Map.of("error", e.getMessage()));
		}
	}
}
