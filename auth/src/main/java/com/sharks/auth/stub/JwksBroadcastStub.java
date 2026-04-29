package com.sharks.auth.stub;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import com.sharks.auth.config.JwksBroadcastProperties;

@Component
@ConditionalOnProperty(name = "auth.stub.jwks-broadcast.enabled", havingValue = "true")
public class JwksBroadcastStub {

	private static final Logger log = LoggerFactory.getLogger(JwksBroadcastStub.class);

	private final JwksBroadcastProperties properties;

	@Value("${spring.security.oauth2.resourceserver.jwt.issuer-uri}")
	private String issuerUri;

	public JwksBroadcastStub(JwksBroadcastProperties properties) {
		this.properties = properties;
	}

	@Scheduled(fixedDelayString = "${auth.stub.jwks-broadcast.interval-ms}")
	public void stubBroadcast() {
		String base = issuerUri.endsWith("/") ? issuerUri.substring(0, issuerUri.length() - 1) : issuerUri;
		String jwksUrl = base + "/.well-known/jwks.json";
		log.info(
				"JWKS broadcast stub: would publish public keys from {} to subscribers (replace with Kafka, SNS, or HTTP fan-out). intervalMs={}",
				jwksUrl, properties.getIntervalMs());
	}
}
