package com.gen.auth.client;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withBadRequest;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import com.gen.auth.config.SupabaseProperties;
import com.gen.auth.exception.SupabaseAuthException;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

class SupabaseAuthClientTest {

	private MockRestServiceServer mockServer;

	private SupabaseAuthClient client;

	@BeforeEach
	void setUp() {
		RestClient.Builder builder = RestClient.builder();
		mockServer = MockRestServiceServer.bindTo(builder).build();
		RestClient restClient = builder.baseUrl("http://localhost").build();
		SupabaseProperties properties = new SupabaseProperties();
		properties.setBaseUrl("http://localhost");
		properties.setAnonKey("test-anon");
		properties.setServiceRoleKey("test-service-role");
		client = new SupabaseAuthClient(restClient, properties);
	}

	@AfterEach
	void tearDown() {
		mockServer.reset();
	}

	@Test
	void signInWithPassword_mapsSuccessBody() {
		mockServer.expect(requestTo("http://localhost/auth/v1/token?grant_type=password"))
			.andExpect(method(HttpMethod.POST))
			.andExpect(header("apikey", "test-anon"))
			.andExpect(content().contentType(MediaType.APPLICATION_JSON))
			.andExpect(content().json("{\"email\":\"a@b.com\",\"password\":\"secret\"}"))
			.andRespond(withSuccess(
				"""
					{"access_token":"at","token_type":"bearer","expires_in":3600,"expires_at":123,"refresh_token":"rt","user":{"id":"u1"}}
					""",
				MediaType.APPLICATION_JSON
			));

		GotrueSessionResponse session = client.signInWithPassword("a@b.com", "secret");

		assertThat(session.accessToken()).isEqualTo("at");
		assertThat(session.tokenType()).isEqualTo("bearer");
		assertThat(session.expiresIn()).isEqualTo(3600L);
		assertThat(session.refreshToken()).isEqualTo("rt");
		assertThat(session.user().get("id").asText()).isEqualTo("u1");
		mockServer.verify();
	}

	@Test
	void signInWithPassword_mapsErrorToSupabaseAuthException() {
		mockServer.expect(requestTo("http://localhost/auth/v1/token?grant_type=password"))
			.andExpect(method(HttpMethod.POST))
			.andRespond(withBadRequest().body("{\"error\":\"invalid_grant\"}"));

		assertThatThrownBy(() -> client.signInWithPassword("a@b.com", "wrong"))
			.isInstanceOf(SupabaseAuthException.class)
			.extracting("statusCode")
			.isEqualTo(400);

		mockServer.verify();
	}

	@Test
	void adminCreateUser_mapsSuccessBodyAndUsesServiceRoleHeaders() {
		mockServer.expect(requestTo("http://localhost/auth/v1/admin/users"))
			.andExpect(method(HttpMethod.POST))
			.andExpect(header("apikey", "test-service-role"))
			.andExpect(header("Authorization", "Bearer test-service-role"))
			.andExpect(content().contentType(MediaType.APPLICATION_JSON))
			.andExpect(content().json("{\"email\":\"new@b.com\",\"password\":\"secret\",\"email_confirm\":true}"))
			.andRespond(withSuccess(
				"""
					{"id":"u-admin-1","email":"new@b.com"}
					""",
				MediaType.APPLICATION_JSON
			));

		GotrueAdminUserResponse user = client.adminCreateUser(
			new GotrueAdminCreateUserRequest("new@b.com", "secret", true));

		assertThat(user.id()).isEqualTo("u-admin-1");
		assertThat(user.email()).isEqualTo("new@b.com");
		mockServer.verify();
	}

	@Test
	void adminCreateUser_mapsErrorToSupabaseAuthException() {
		mockServer.expect(requestTo("http://localhost/auth/v1/admin/users"))
			.andExpect(method(HttpMethod.POST))
			.andRespond(withBadRequest().body("{\"error\":\"email_exists\"}"));

		assertThatThrownBy(() -> client.adminCreateUser(
			new GotrueAdminCreateUserRequest("x@b.com", "p", true)))
			.isInstanceOf(SupabaseAuthException.class)
			.extracting("statusCode")
			.isEqualTo(400);

		mockServer.verify();
	}
}
