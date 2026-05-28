package com.farm.backend.repository;

import com.farm.backend.entity.User;
import com.farm.backend.entity.Role;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.List;

public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByEmail(String email);

    boolean existsByEmail(String email);

    List<User> findByRole(Role role);

    List<User> findByRoleAndFaceRegisteredTrue(Role role);

    Optional<User> findByActivationToken(String token);
}
