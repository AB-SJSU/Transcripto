package com.sharks.auth.web;

import java.util.HashMap;
import java.util.Map;

import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
public class UserController {

	@GetMapping("/me")
	public Map<String, Object> me(@AuthenticationPrincipal Jwt jwt) {
		Map<String, Object> body = new HashMap<>();
		body.put("sub", jwt.getSubject());
		body.put("iss", jwt.getIssuer() != null ? jwt.getIssuer().toString() : null);
		return body;
	}
}
