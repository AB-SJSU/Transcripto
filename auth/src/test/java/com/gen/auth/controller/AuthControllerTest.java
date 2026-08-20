package com.gen.auth.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.gen.auth.dto.LoginRequest;
import com.gen.auth.dto.LoginResponse;
import com.gen.auth.dto.SignupRequest;
import com.gen.auth.dto.SignupResponse;
import com.gen.auth.exception.AuthExceptionHandler;
import com.gen.auth.exception.SupabaseAuthException;
import com.gen.auth.service.AuthService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import tools.jackson.databind.json.JsonMapper;

@WebMvcTest(AuthController.class)
@Import(AuthExceptionHandler.class)
class AuthControllerTest {

	private static final JsonMapper JSON = JsonMapper.builder().build();

	@Autowired
	MockMvc mockMvc;

	@MockitoBean
	AuthService authService;

	@Test
	void login_ok_returnsSession() throws Exception {
		var user = JSON.readTree("{\"id\":\"550e8400-e29b-41d4-a716-446655440000\"}");
		when(authService.login(any(LoginRequest.class))).thenReturn(
			new LoginResponse("access", "bearer", 3600L, 999L, "refresh", user)
		);

		mockMvc.perform(post("/api/v1/auth/login")
				.contentType(MediaType.APPLICATION_JSON)
				.content("{\"email\":\"u@example.com\",\"password\":\"p\"}"))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.accessToken").value("access"))
			.andExpect(jsonPath("$.tokenType").value("bearer"))
			.andExpect(jsonPath("$.expiresIn").value(3600))
			.andExpect(jsonPath("$.refreshToken").value("refresh"));

		verify(authService).login(any(LoginRequest.class));
	}

	@Test
	void login_supabaseUnauthorized_returns401() throws Exception {
		when(authService.login(any(LoginRequest.class)))
			.thenThrow(new SupabaseAuthException(400, "{\"error\":\"invalid_grant\"}"));

		mockMvc.perform(post("/api/v1/auth/login")
				.contentType(MediaType.APPLICATION_JSON)
				.content("{\"email\":\"u@example.com\",\"password\":\"bad\"}"))
			.andExpect(status().isUnauthorized());

		verify(authService).login(any(LoginRequest.class));
	}

	@Test
	void login_validationError_returns400() throws Exception {
		mockMvc.perform(post("/api/v1/auth/login")
				.contentType(MediaType.APPLICATION_JSON)
				.content("{\"email\":\"not-an-email\",\"password\":\"x\"}"))
			.andExpect(status().isBadRequest());
	}

	@Test
	void signup_ok_returnsUser() throws Exception {
		when(authService.signup(any(SignupRequest.class))).thenReturn(
			new SignupResponse("550e8400-e29b-41d4-a716-446655440000", "new@example.com")
		);

		mockMvc.perform(post("/api/v1/auth/signup")
				.contentType(MediaType.APPLICATION_JSON)
				.content("{\"email\":\"new@example.com\",\"password\":\"secret\"}"))
			.andExpect(status().isCreated())
			.andExpect(jsonPath("$.id").value("550e8400-e29b-41d4-a716-446655440000"))
			.andExpect(jsonPath("$.email").value("new@example.com"));

		verify(authService).signup(any(SignupRequest.class));
	}

	@Test
	void signup_validationError_returns400() throws Exception {
		mockMvc.perform(post("/api/v1/auth/signup")
				.contentType(MediaType.APPLICATION_JSON)
				.content("{\"email\":\"not-an-email\",\"password\":\"x\"}"))
			.andExpect(status().isBadRequest());
	}

	@Test
	void signup_supabaseDuplicate_returns422() throws Exception {
		when(authService.signup(any(SignupRequest.class)))
			.thenThrow(new SupabaseAuthException(422, "{\"error\":\"user_already_exists\"}"));

		mockMvc.perform(post("/api/v1/auth/signup")
				.contentType(MediaType.APPLICATION_JSON)
				.content("{\"email\":\"dup@example.com\",\"password\":\"p\"}"))
			.andExpect(status().isUnprocessableEntity());

		verify(authService).signup(any(SignupRequest.class));
	}
}
