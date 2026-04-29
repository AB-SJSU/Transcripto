package com.sharks.auth.client;

import java.util.Map;
import java.util.UUID;

import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import com.sharks.auth.config.SupabaseProperties;

@Component
public class SupabaseAdminClient {

	private final SupabaseProperties supabaseProperties;
	private final RestClient restClient;

	public SupabaseAdminClient(SupabaseProperties supabaseProperties) {
		this(supabaseProperties, RestClient.builder().baseUrl(supabaseProperties.getUrl()).build());
	}

	public SupabaseAdminClient(SupabaseProperties supabaseProperties, RestClient restClient) {
		this.supabaseProperties = supabaseProperties;
		this.restClient = restClient;
	}

	/**
	 * Creates a user via Auth Admin API. Uses service role for {@code apikey} and Bearer.
	 */
	@SuppressWarnings("unchecked")
	public UUID createUserWithEmailPassword(String email, String password) {
		String key = supabaseProperties.getServiceRoleKey();
		if (key == null || key.isEmpty()) {
			throw new IllegalStateException("supabase.service-role-key is not configured");
		}
		try {
			Map<String, Object> body = restClient.post()
					.uri("/auth/v1/admin/users")
					.header("apikey", key)
					.header(HttpHeaders.AUTHORIZATION, "Bearer " + key)
					.header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
					.body(Map.of(
							"email", email,
							"password", password,
							"email_confirm", true))
					.retrieve()
					.body(Map.class);
			if (body == null || body.get("id") == null) {
				throw new IllegalStateException("Admin API response missing id");
			}
			Object id = body.get("id");
			if (id instanceof String s) {
				return UUID.fromString(s);
			}
			throw new IllegalStateException("Unexpected id type in Admin API response");
		} catch (RestClientException e) {
			throw e;
		}
	}
}
