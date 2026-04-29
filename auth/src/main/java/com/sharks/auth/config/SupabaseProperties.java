package com.sharks.auth.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "supabase")
public class SupabaseProperties {

	/**
	 * Project URL without trailing slash, e.g. http://127.0.0.1:54321 or https://xxx.supabase.co
	 */
	private String url = "http://127.0.0.1:54321";

	/**
	 * Public anon key (used for Auth API password grant from this service).
	 */
	private String anonKey = "";

	/**
	 * Service role key for Auth Admin API (create user, etc.). Must not be exposed to clients.
	 */
	private String serviceRoleKey = "";

	public String getUrl() {
		return url;
	}

	public void setUrl(String url) {
		this.url = url;
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
