package com.gen.auth.client;

import com.fasterxml.jackson.annotation.JsonProperty;

public record GotrueAdminCreateUserRequest(
	String email,
	String password,
	@JsonProperty("email_confirm") boolean emailConfirm
) {
}
