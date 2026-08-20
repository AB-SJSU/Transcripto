package com.gen.auth.dto;

import tools.jackson.databind.JsonNode;

public record LoginResponse(
	String accessToken,
	String tokenType,
	Long expiresIn,
	Long expiresAt,
	String refreshToken,
	JsonNode user
) {
	public static LoginResponse fromGotrue(com.gen.auth.client.GotrueSessionResponse s) {
		return new LoginResponse(
			s.accessToken(),
			s.tokenType(),
			s.expiresIn(),
			s.expiresAt(),
			s.refreshToken(),
			s.user()
		);
	}
}
