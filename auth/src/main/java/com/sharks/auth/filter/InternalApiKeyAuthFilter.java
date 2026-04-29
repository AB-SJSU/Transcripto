package com.sharks.auth.filter;

import java.io.IOException;
import java.util.List;

import org.springframework.http.HttpHeaders;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import com.sharks.auth.config.InternalApiProperties;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@Component
public class InternalApiKeyAuthFilter extends OncePerRequestFilter {

	public static final String HEADER_INTERNAL_API_KEY = "X-Internal-Api-Key";

	private final InternalApiProperties internalApiProperties;

	public InternalApiKeyAuthFilter(InternalApiProperties internalApiProperties) {
		this.internalApiProperties = internalApiProperties;
	}

	@Override
	protected boolean shouldNotFilter(@NonNull HttpServletRequest request) {
		return !request.getServletPath().startsWith("/internal/");
	}

	@Override
	protected void doFilterInternal(@NonNull HttpServletRequest request, @NonNull HttpServletResponse response,
			@NonNull FilterChain filterChain) throws ServletException, IOException {
		String provided = request.getHeader(HEADER_INTERNAL_API_KEY);
		String expected = internalApiProperties.getApiKey();
		if (expected == null || expected.isEmpty() || !expected.equals(provided)) {
			response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
			response.setHeader(HttpHeaders.WWW_AUTHENTICATE, "InternalApiKey");
			return;
		}
		var auth = new UsernamePasswordAuthenticationToken("internal", null,
				List.of(new SimpleGrantedAuthority("ROLE_INTERNAL")));
		SecurityContextHolder.getContext().setAuthentication(auth);
		try {
			filterChain.doFilter(request, response);
		} finally {
			SecurityContextHolder.clearContext();
		}
	}
}
