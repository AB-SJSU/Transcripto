package com.sharks.auth.service;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import com.sharks.auth.client.SupabaseAdminClient;
import com.sharks.auth.client.SupabaseAuthClient;

@Service
public class AuthService {

	private static final Logger log = LoggerFactory.getLogger(AuthService.class);

	private final SupabaseAuthClient supabaseAuthClient;
	private final SupabaseAdminClient supabaseAdminClient;

	public AuthService(SupabaseAuthClient supabaseAuthClient, SupabaseAdminClient supabaseAdminClient) {
		this.supabaseAuthClient = supabaseAuthClient;
		this.supabaseAdminClient = supabaseAdminClient;
	}

	/**
	 * Password login via Supabase Auth (anon key grant).
	 */
	public Map<String, Object> login(String email, String password) {
		validateCredentials(email, password);
		String trimmedEmail = email.trim();
		return supabaseAuthClient.signInWithPassword(trimmedEmail, password);
	}

	/**
	 * Creates user via Admin API, then issues session tokens via password grant.
	 * Response includes Supabase token fields plus {@code user_id}.
	 */
	public Map<String, Object> signup(String email, String password) {
		validateCredentials(email, password);
		String trimmedEmail = email.trim();
		UUID userId = supabaseAdminClient.createUserWithEmailPassword(trimmedEmail, password);
		log.info("Signed up Supabase user id={}", userId);
		Map<String, Object> tokens = supabaseAuthClient.signInWithPassword(trimmedEmail, password);
		Map<String, Object> body = new HashMap<>(tokens);
		body.put("user_id", userId.toString());
		return body;
	}

	private static void validateCredentials(String email, String password) {
		if (!StringUtils.hasText(email)) {
			throw new IllegalArgumentException("email is required");
		}
		if (!StringUtils.hasText(password)) {
			throw new IllegalArgumentException("password is required");
		}
	}
}
