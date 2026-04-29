package com.sharks.auth.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.sharks.auth.client.SupabaseAdminClient;

@ExtendWith(MockitoExtension.class)
class UserProvisioningServiceTest {

	private static final UUID NEW_USER = UUID.fromString("11111111-1111-1111-1111-111111111111");

	@Mock
	private SupabaseAdminClient supabaseAdminClient;

	private UserProvisioningService userProvisioningService;

	@BeforeEach
	void setUp() {
		userProvisioningService = new UserProvisioningService(supabaseAdminClient);
	}

	@Test
	void trimsEmailBeforeCreate() {
		when(supabaseAdminClient.createUserWithEmailPassword("a@b.com", "secret")).thenReturn(NEW_USER);

		UUID id = userProvisioningService.provisionUser("  a@b.com  ", "secret");

		assertThat(id).isEqualTo(NEW_USER);
		verify(supabaseAdminClient).createUserWithEmailPassword("a@b.com", "secret");
	}

	@Test
	void rejectsBlankEmail() {
		assertThatThrownBy(() -> userProvisioningService.provisionUser("  ", "secret"))
				.isInstanceOf(IllegalArgumentException.class)
				.hasMessageContaining("email");
		verify(supabaseAdminClient, never()).createUserWithEmailPassword(any(), any());
	}

	@Test
	void rejectsBlankPassword() {
		assertThatThrownBy(() -> userProvisioningService.provisionUser("a@b.com", "   "))
				.isInstanceOf(IllegalArgumentException.class)
				.hasMessageContaining("password");
		verify(supabaseAdminClient, never()).createUserWithEmailPassword(any(), any());
	}
}
