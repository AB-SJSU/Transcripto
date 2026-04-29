package com.sharks.auth.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "auth.stub.jwks-broadcast")
public class JwksBroadcastProperties {

	/**
	 * When true, periodically logs a stub "would broadcast JWKS" message.
	 */
	private boolean enabled = false;

	/**
	 * Fixed delay between stub runs (ms).
	 */
	private long intervalMs = 3600_000L;

	public boolean isEnabled() {
		return enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}

	public long getIntervalMs() {
		return intervalMs;
	}

	public void setIntervalMs(long intervalMs) {
		this.intervalMs = intervalMs;
	}
}
