package com.sharks.auth.filter;

import java.io.IOException;
import java.util.UUID;

import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class RequestIdFilter extends OncePerRequestFilter {

	public static final String REQUEST_ID_MDC = "requestId";
	public static final String HEADER_REQUEST_ID = "X-Request-Id";

	@Override
	protected void doFilterInternal(@NonNull HttpServletRequest request, @NonNull HttpServletResponse response,
			@NonNull FilterChain filterChain) throws ServletException, IOException {
		String id = request.getHeader(HEADER_REQUEST_ID);
		if (id == null || id.isBlank()) {
			id = UUID.randomUUID().toString();
		}
		MDC.put(REQUEST_ID_MDC, id);
		response.setHeader(HEADER_REQUEST_ID, id);
		try {
			filterChain.doFilter(request, response);
		} finally {
			MDC.remove(REQUEST_ID_MDC);
		}
	}
}
