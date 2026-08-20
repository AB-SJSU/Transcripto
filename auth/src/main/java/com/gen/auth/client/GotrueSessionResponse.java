package com.gen.auth.client;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import tools.jackson.databind.JsonNode;

@JsonIgnoreProperties(ignoreUnknown = true)
public record GotrueSessionResponse(
	@JsonProperty("access_token") String accessToken,
	@JsonProperty("token_type") String tokenType,
	@JsonProperty("expires_in") Long expiresIn,
	@JsonProperty("expires_at") Long expiresAt,
	@JsonProperty("refresh_token") String refreshToken,
	@JsonProperty("user") JsonNode user
) {
}
