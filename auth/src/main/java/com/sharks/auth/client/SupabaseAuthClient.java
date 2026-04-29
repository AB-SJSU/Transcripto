package com.sharks.auth.client;

import java.util.Map;

import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import com.sharks.auth.config.SupabaseProperties;

@Component
public class SupabaseAuthClient {

	private final SupabaseProperties supabaseProperties;
	private final RestClient restClient;

	public SupabaseAuthClient(SupabaseProperties supabaseProperties) {
		this.supabaseProperties = supabaseProperties;
		this.restClient = RestClient.builder().baseUrl(supabaseProperties.getUrl()).build();
	}

	/**
	 * Calls Supabase Auth password grant; returns parsed JSON body (access_token, refresh_token, etc.).
	 */
	@SuppressWarnings("unchecked")
	public Map<String, Object> signInWithPassword(String email, String password) {
		String anonKey = supabaseProperties.getAnonKey();
		if (anonKey == null || anonKey.isEmpty()) {
			throw new IllegalStateException("supabase.anon-key is not configured");
		}
		try {
			return restClient.post()
					.uri("/auth/v1/token?grant_type=password")
					.header("apikey", anonKey)
					.header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
					.body(Map.of("email", email, "password", password))
					.retrieve()
					.body(Map.class);
		} catch (RestClientException e) {
			throw e;
		}
	}
}
