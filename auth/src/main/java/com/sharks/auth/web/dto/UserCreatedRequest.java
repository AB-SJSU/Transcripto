package com.sharks.auth.web.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * Body for internal user provisioning ({@code POST /internal/jobs/user-created}).
 */
public class UserCreatedRequest {

	@NotBlank
	private String email;

	@NotBlank
	private String password;

	public String getEmail() {
		return email;
	}

	public void setEmail(String email) {
		this.email = email;
	}

	public String getPassword() {
		return password;
	}

	public void setPassword(String password) {
		this.password = password;
	}
}
