package com.gen.auth.exception;

public class SupabaseAuthException extends RuntimeException {

	private final int statusCode;

	private final String responseBody;

	public SupabaseAuthException(int statusCode, String responseBody) {
		super("Supabase Auth HTTP " + statusCode);
		this.statusCode = statusCode;
		this.responseBody = responseBody;
	}

	public int getStatusCode() {
		return statusCode;
	}

	public String getResponseBody() {
		return responseBody;
	}
}
