package com.gen.auth.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "supabase")
public class SupabaseProperties {

	private String baseUrl = "http://localhost:8000";

	/**
	 * Supabase anonymous (publishable) API key — sent as {@code apikey} on GoTrue requests.
	 */
	private String anonKey = "";

	/**
	 * Service role JWT — required for GoTrue admin routes (e.g. create user). Never expose to clients.
	 */
	private String serviceRoleKey = "";

	public String getBaseUrl() {
		return baseUrl;
	}

	public void setBaseUrl(String baseUrl) {
		this.baseUrl = baseUrl;
	}

	public String getAnonKey() {
		return anonKey;
	}

	public void setAnonKey(String anonKey) {
		this.anonKey = anonKey;
	}

	public String getServiceRoleKey() {
		return serviceRoleKey;
	}

	public void setServiceRoleKey(String serviceRoleKey) {
		this.serviceRoleKey = serviceRoleKey;
	}
}
