package com.gen.auth.client;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public record GotrueAdminUserResponse(String id, String email) {
}
