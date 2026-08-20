package com.gen.auth.model;

public enum AppRole {
	CUSTOMER("customer"),
	APP_ADMIN("app_admin"),
	ORGANIZATION("organization");

	private final String dbValue;

	AppRole(String dbValue) {
		this.dbValue = dbValue;
	}

	public String getDbValue() {
		return dbValue;
	}

	public static AppRole fromDbValue(String value) {
		if (value == null) {
			return null;
		}
		for (AppRole r : values()) {
			if (r.dbValue.equals(value)) {
				return r;
			}
		}
		throw new IllegalArgumentException("Unknown app_role: " + value);
	}
}
