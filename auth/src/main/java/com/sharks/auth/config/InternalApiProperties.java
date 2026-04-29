package com.sharks.auth.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "auth.internal")
public class InternalApiProperties {

	/**
	 * Shared secret for X-Internal-Api-Key on /internal/** routes.
	 */
	private String apiKey = "change-me";

	public String getApiKey() {
		return apiKey;
	}

	public void setApiKey(String apiKey) {
		this.apiKey = apiKey;
	}
}
