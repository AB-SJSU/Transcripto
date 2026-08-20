package com.gen.auth.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
@EnableConfigurationProperties(SupabaseProperties.class)
public class SupabaseConfig {

	@Bean
	public RestClient supabaseRestClient(SupabaseProperties properties) {
		String base = properties.getBaseUrl().replaceAll("/+$", "");
		return RestClient.builder().baseUrl(base).build();
	}

}
