package com.sharks.auth.internal;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.MediaType;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.client.RestClientResponseException;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sharks.auth.config.InternalApiProperties;
import com.sharks.auth.config.SecurityConfig;
import com.sharks.auth.filter.InternalApiKeyAuthFilter;
import com.sharks.auth.service.AuthService;

@WebMvcTest(controllers = InternalAuthController.class)
@Import({ SecurityConfig.class, InternalApiKeyAuthFilter.class })
@EnableConfigurationProperties(InternalApiProperties.class)
@TestPropertySource(properties = {
		"auth.internal.api-key=test-internal-key",
		"spring.security.oauth2.resourceserver.jwt.issuer-uri=https://example.test/auth/v1"
})
class InternalAuthControllerTest {

	private static final String API_KEY = "test-internal-key";

	@Autowired
	private MockMvc mockMvc;

	@Autowired
	private ObjectMapper objectMapper;

	@MockBean
	private JwtDecoder jwtDecoder;

	@MockBean
	private AuthService authService;

	@Test
	void loginReturns200WithTokensWhenApiKeyPresent() throws Exception {
		Map<String, Object> tokens = new LinkedHashMap<>();
		tokens.put("access_token", "at");
		tokens.put("refresh_token", "rt");
		when(authService.login(eq("a@b.com"), eq("secret123"))).thenReturn(tokens);

		mockMvc.perform(post("/internal/auth/login")
						.header(InternalApiKeyAuthFilter.HEADER_INTERNAL_API_KEY, API_KEY)
						.contentType(MediaType.APPLICATION_JSON)
						.content(objectMapper.writeValueAsString(Map.of(
								"email", "a@b.com",
								"password", "secret123"))))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.access_token").value("at"))
				.andExpect(jsonPath("$.refresh_token").value("rt"));

		verify(authService).login("a@b.com", "secret123");
	}

	@Test
	void loginReturns401WhenApiKeyMissing() throws Exception {
		mockMvc.perform(post("/internal/auth/login")
						.contentType(MediaType.APPLICATION_JSON)
						.content(objectMapper.writeValueAsString(Map.of(
								"email", "a@b.com",
								"password", "secret123"))))
				.andExpect(status().isUnauthorized());
	}

	@Test
	void loginReturns401WhenSupabaseRejectsCredentials() throws Exception {
		RestClientResponseException ex = mock(RestClientResponseException.class);
		when(ex.getStatusCode()).thenReturn(HttpStatusCode.valueOf(401));
		when(ex.getResponseBodyAsString()).thenReturn("{\"error\":\"invalid\"}");
		when(authService.login(anyString(), anyString())).thenThrow(ex);

		mockMvc.perform(post("/internal/auth/login")
						.header(InternalApiKeyAuthFilter.HEADER_INTERNAL_API_KEY, API_KEY)
						.contentType(MediaType.APPLICATION_JSON)
						.content(objectMapper.writeValueAsString(Map.of(
								"email", "a@b.com",
								"password", "wrong"))))
				.andExpect(status().isUnauthorized());
	}

	@Test
	void loginReturns400WhenValidationFails() throws Exception {
		mockMvc.perform(post("/internal/auth/login")
						.header(InternalApiKeyAuthFilter.HEADER_INTERNAL_API_KEY, API_KEY)
						.contentType(MediaType.APPLICATION_JSON)
						.content(objectMapper.writeValueAsString(Map.of(
								"email", "",
								"password", "secret123"))))
				.andExpect(status().isBadRequest());
	}

	@Test
	void signupReturns201WithUserIdAndTokens() throws Exception {
		UUID id = UUID.fromString("22222222-2222-2222-2222-222222222222");
		Map<String, Object> body = new LinkedHashMap<>();
		body.put("access_token", "at");
		body.put("refresh_token", "rt");
		body.put("user_id", id.toString());
		when(authService.signup(eq("new@b.com"), eq("secret12"))).thenReturn(body);

		mockMvc.perform(post("/internal/auth/signup")
						.header(InternalApiKeyAuthFilter.HEADER_INTERNAL_API_KEY, API_KEY)
						.contentType(MediaType.APPLICATION_JSON)
						.content(objectMapper.writeValueAsString(Map.of(
								"email", "new@b.com",
								"password", "secret12"))))
				.andExpect(status().isCreated())
				.andExpect(jsonPath("$.user_id").value(id.toString()))
				.andExpect(jsonPath("$.access_token").value("at"));

		verify(authService).signup("new@b.com", "secret12");
	}

	@Test
	void signupReturns409WhenUserAlreadyExists() throws Exception {
		RestClientResponseException ex = mock(RestClientResponseException.class);
		when(ex.getStatusCode()).thenReturn(HttpStatusCode.valueOf(422));
		when(ex.getResponseBodyAsString()).thenReturn("{\"msg\":\"User already registered\"}");
		when(authService.signup(anyString(), anyString())).thenThrow(ex);

		mockMvc.perform(post("/internal/auth/signup")
						.header(InternalApiKeyAuthFilter.HEADER_INTERNAL_API_KEY, API_KEY)
						.contentType(MediaType.APPLICATION_JSON)
						.content(objectMapper.writeValueAsString(Map.of(
								"email", "dup@b.com",
								"password", "secret12"))))
				.andExpect(status().isConflict());
	}

	@Test
	void signupReturns400WhenPasswordTooShort() throws Exception {
		mockMvc.perform(post("/internal/auth/signup")
						.header(InternalApiKeyAuthFilter.HEADER_INTERNAL_API_KEY, API_KEY)
						.contentType(MediaType.APPLICATION_JSON)
						.content(objectMapper.writeValueAsString(Map.of(
								"email", "x@b.com",
								"password", "short"))))
				.andExpect(status().isBadRequest());
	}
}
