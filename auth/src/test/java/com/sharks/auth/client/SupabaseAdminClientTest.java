package com.sharks.auth.client;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.client.matchers.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.matchers.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.matchers.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import com.sharks.auth.config.SupabaseProperties;

class SupabaseAdminClientTest {

	private static final UUID USER_ID = UUID.fromString("22222222-2222-2222-2222-222222222222");

	@Test
	void createUserParsesIdFromResponse() {
		SupabaseProperties properties = new SupabaseProperties();
		properties.setUrl("http://127.0.0.1:9");
		properties.setServiceRoleKey("test-service-role");

		RestClient.Builder builder = RestClient.builder().baseUrl(properties.getUrl());
		MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
		RestClient restClient = builder.build();

		server.expect(requestTo("http://127.0.0.1:9/auth/v1/admin/users"))
				.andExpect(method(HttpMethod.POST))
				.andExpect(header("apikey", "test-service-role"))
				.andExpect(header(HttpHeaders.AUTHORIZATION, "Bearer test-service-role"))
				.andRespond(withSuccess("{\"id\":\"" + USER_ID + "\"}", APPLICATION_JSON));

		SupabaseAdminClient client = new SupabaseAdminClient(properties, restClient);
		assertThat(client.createUserWithEmailPassword("a@b.com", "secret")).isEqualTo(USER_ID);
		server.verify();
	}

	@Test
	void createUserFailsWhenServiceRoleMissing() {
		SupabaseProperties properties = new SupabaseProperties();
		properties.setUrl("http://127.0.0.1:9");
		properties.setServiceRoleKey("");

		SupabaseAdminClient client = new SupabaseAdminClient(properties,
				RestClient.builder().baseUrl(properties.getUrl()).build());

		assertThatThrownBy(() -> client.createUserWithEmailPassword("a@b.com", "x"))
				.isInstanceOf(IllegalStateException.class)
				.hasMessageContaining("service-role-key");
	}
}
