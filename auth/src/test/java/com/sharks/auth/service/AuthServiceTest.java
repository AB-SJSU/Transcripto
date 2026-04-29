package com.sharks.auth.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.sharks.auth.client.SupabaseAdminClient;
import com.sharks.auth.client.SupabaseAuthClient;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

	private static final UUID NEW_USER = UUID.fromString("33333333-3333-3333-3333-333333333333");

	@Mock
	private SupabaseAuthClient supabaseAuthClient;

	@Mock
	private SupabaseAdminClient supabaseAdminClient;

	private AuthService authService;

	@BeforeEach
	void setUp() {
		authService = new AuthService(supabaseAuthClient, supabaseAdminClient);
	}

	@Test
	void loginDelegatesToSupabaseAuthClient() {
		Map<String, Object> tokens = new LinkedHashMap<>();
		tokens.put("access_token", "at");
		when(supabaseAuthClient.signInWithPassword("u@b.com", "pw")).thenReturn(tokens);

		Map<String, Object> result = authService.login("u@b.com", "pw");

		assertThat(result).containsEntry("access_token", "at");
		verify(supabaseAuthClient).signInWithPassword("u@b.com", "pw");
	}

	@Test
	void loginTrimsEmail() {
		Map<String, Object> tokens = Map.of("access_token", "x");
		when(supabaseAuthClient.signInWithPassword("a@b.com", "pw")).thenReturn(tokens);

		authService.login("  a@b.com  ", "pw");

		verify(supabaseAuthClient).signInWithPassword("a@b.com", "pw");
	}

	@Test
	void signupCreatesUserThenSignsInAndAddsUserId() {
		Map<String, Object> tokens = new LinkedHashMap<>();
		tokens.put("access_token", "at");
		tokens.put("refresh_token", "rt");
		when(supabaseAdminClient.createUserWithEmailPassword("new@b.com", "secret12")).thenReturn(NEW_USER);
		when(supabaseAuthClient.signInWithPassword("new@b.com", "secret12")).thenReturn(tokens);

		Map<String, Object> result = authService.signup("new@b.com", "secret12");

		assertThat(result).containsEntry("access_token", "at");
		assertThat(result).containsEntry("refresh_token", "rt");
		assertThat(result).containsEntry("user_id", NEW_USER.toString());
		verify(supabaseAdminClient).createUserWithEmailPassword("new@b.com", "secret12");
		verify(supabaseAuthClient).signInWithPassword("new@b.com", "secret12");
	}

	@Test
	void signupTrimsEmail() {
		Map<String, Object> tokens = Map.of("access_token", "x");
		when(supabaseAdminClient.createUserWithEmailPassword("a@b.com", "secret12")).thenReturn(NEW_USER);
		when(supabaseAuthClient.signInWithPassword("a@b.com", "secret12")).thenReturn(tokens);

		authService.signup("  a@b.com  ", "secret12");

		verify(supabaseAdminClient).createUserWithEmailPassword("a@b.com", "secret12");
		verify(supabaseAuthClient).signInWithPassword("a@b.com", "secret12");
	}

	@Test
	void rejectsBlankEmailOnLogin() {
		assertThatThrownBy(() -> authService.login("   ", "pw"))
				.isInstanceOf(IllegalArgumentException.class)
				.hasMessageContaining("email");
	}

	@Test
	void rejectsBlankPasswordOnSignup() {
		assertThatThrownBy(() -> authService.signup("a@b.com", "   "))
				.isInstanceOf(IllegalArgumentException.class)
				.hasMessageContaining("password");
	}
}
