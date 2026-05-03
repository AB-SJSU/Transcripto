package com.gen.auth.service;

import com.gen.auth.client.GotrueAdminCreateUserRequest;
import com.gen.auth.client.GotrueAdminUserResponse;
import com.gen.auth.client.SupabaseAuthClient;
import com.gen.auth.dto.LoginRequest;
import com.gen.auth.dto.LoginResponse;
import com.gen.auth.dto.SignupRequest;
import com.gen.auth.dto.SignupResponse;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

	private final SupabaseAuthClient supabaseAuthClient;

	public AuthService(SupabaseAuthClient supabaseAuthClient) {
		this.supabaseAuthClient = supabaseAuthClient;
	}

	public LoginResponse login(LoginRequest request) {
		var session = supabaseAuthClient.signInWithPassword(request.getEmail(), request.getPassword());
		return LoginResponse.fromGotrue(session);
	}

	public SignupResponse signup(SignupRequest request) {
		var user = createUser(request.getEmail(), request.getPassword());
		return new SignupResponse(user.id(), user.email());
	}

	/**
	 * Creates a Supabase Auth user via the GoTrue admin API.
	 * <p>
	 * Email is marked confirmed in this call ({@code email_confirm: true}) so no confirmation email flow runs.
	 * TODO: When enabling product email verification, set {@code email_confirm} to false here and configure GoTrue mailer / templates accordingly.
	 */
	public GotrueAdminUserResponse createUser(String email, String password) {
		var body = new GotrueAdminCreateUserRequest(email, password, true);
		return supabaseAuthClient.adminCreateUser(body);
	}
}
