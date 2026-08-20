package com.gen.auth.client;

import com.gen.auth.config.SupabaseProperties;
import com.gen.auth.exception.SupabaseAuthException;
import java.nio.charset.StandardCharsets;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

@Component
public class SupabaseAuthClient {

	private final RestClient restClient;

	private final SupabaseProperties properties;

	public SupabaseAuthClient(RestClient supabaseRestClient, SupabaseProperties properties) {
		this.restClient = supabaseRestClient;
		this.properties = properties;
	}

	/**
	 * Password grant against GoTrue: {@code POST /auth/v1/token?grant_type=password}.
	 */
	public GotrueSessionResponse signInWithPassword(String email, String password) {
		try {
			return restClient.post()
				.uri("/auth/v1/token?grant_type=password")
				.header("apikey", properties.getAnonKey())
				.accept(MediaType.APPLICATION_JSON)
				.contentType(MediaType.APPLICATION_JSON)
				.body(new GotruePasswordGrantRequest(email, password))
				.retrieve()
				.body(GotrueSessionResponse.class);
		} catch (RestClientResponseException e) {
			String body = e.getResponseBodyAsString(StandardCharsets.UTF_8);
			throw new SupabaseAuthException(e.getStatusCode().value(), body);
		}
	}

	/**
	 * GoTrue admin API: {@code POST /auth/v1/admin/users} (requires service role).
	 */
	public GotrueAdminUserResponse adminCreateUser(GotrueAdminCreateUserRequest request) {
		String key = properties.getServiceRoleKey();
		try {
			return restClient.post()
				.uri("/auth/v1/admin/users")
				.header("apikey", key)
				.header("Authorization", "Bearer " + key)
				.accept(MediaType.APPLICATION_JSON)
				.contentType(MediaType.APPLICATION_JSON)
				.body(request)
				.retrieve()
				.body(GotrueAdminUserResponse.class);
		} catch (RestClientResponseException e) {
			String body = e.getResponseBodyAsString(StandardCharsets.UTF_8);
			throw new SupabaseAuthException(e.getStatusCode().value(), body);
		}
	}
}
