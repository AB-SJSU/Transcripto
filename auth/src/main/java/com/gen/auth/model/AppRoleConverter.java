package com.gen.auth.model;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

@Converter(autoApply = true)
public class AppRoleConverter implements AttributeConverter<AppRole, String> {

	@Override
	public String convertToDatabaseColumn(AppRole attribute) {
		return attribute == null ? null : attribute.getDbValue();
	}

	@Override
	public AppRole convertToEntityAttribute(String dbData) {
		return dbData == null ? null : AppRole.fromDbValue(dbData);
	}
}
