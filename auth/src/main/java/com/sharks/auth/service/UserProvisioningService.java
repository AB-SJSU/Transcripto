package com.sharks.auth.service;

import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import com.sharks.auth.client.SupabaseAdminClient;

@Service
public class UserProvisioningService {

	private static final Logger log = LoggerFactory.getLogger(UserProvisioningService.class);

	private final SupabaseAdminClient supabaseAdminClient;

	public UserProvisioningService(SupabaseAdminClient supabaseAdminClient) {
		this.supabaseAdminClient = supabaseAdminClient;
	}

	/**
	 * Creates the Supabase user with email/password only.
	 */
	public UUID provisionUser(String email, String password) {
		if (!StringUtils.hasText(email)) {
			throw new IllegalArgumentException("email is required");
		}
		if (!StringUtils.hasText(password)) {
			throw new IllegalArgumentException("password is required");
		}

		String trimmedEmail = email.trim();
		UUID userId = supabaseAdminClient.createUserWithEmailPassword(trimmedEmail, password);
		log.info("Provisioned Supabase user id={}", userId);

		return userId;
	}
}
