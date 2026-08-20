package com.gen.auth.repo;

import com.gen.auth.model.AppRole;
import com.gen.auth.model.UserRole;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRoleRepository extends JpaRepository<UserRole, UUID> {

	List<UserRole> findByUserId(UUID userId);

	boolean existsByUserIdAndRole(UUID userId, AppRole role);
}
