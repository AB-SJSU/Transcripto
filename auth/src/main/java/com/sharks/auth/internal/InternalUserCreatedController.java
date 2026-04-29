package com.sharks.auth.internal;

import java.util.Map;
import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sharks.auth.service.UserProvisioningService;
import com.sharks.auth.web.dto.UserCreatedRequest;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/internal/jobs")
public class InternalUserCreatedController {

	private static final Logger log = LoggerFactory.getLogger(InternalUserCreatedController.class);

	private final UserProvisioningService userProvisioningService;

	public InternalUserCreatedController(UserProvisioningService userProvisioningService) {
		this.userProvisioningService = userProvisioningService;
	}

	@PostMapping("/user-created")
	public ResponseEntity<Map<String, String>> userCreated(@Valid @RequestBody UserCreatedRequest body) {
		log.info("Accepted user_created job");
		UUID userId = userProvisioningService.provisionUser(body.getEmail(), body.getPassword());
		return ResponseEntity.accepted()
				.body(Map.of("jobId", UUID.randomUUID().toString(), "status", "accepted", "userId", userId.toString()));
	}
}
