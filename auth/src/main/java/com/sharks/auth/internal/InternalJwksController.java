package com.sharks.auth.internal;

import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal")
public class InternalJwksController {

	@Value("${spring.security.oauth2.resourceserver.jwt.issuer-uri}")
	private String issuerUri;

	@GetMapping("/jwks-metadata")
	public Map<String, String> jwksMetadata() {
		String base = issuerUri.endsWith("/") ? issuerUri.substring(0, issuerUri.length() - 1) : issuerUri;
		String jwksUrl = base + "/.well-known/jwks.json";
		return Map.of("issuer", issuerUri, "jwksUrl", jwksUrl, "note", "stub metadata for ops");
	}
}
