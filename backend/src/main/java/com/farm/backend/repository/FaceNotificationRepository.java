package com.farm.backend.repository;

import com.farm.backend.entity.FaceNotification;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface FaceNotificationRepository extends JpaRepository<FaceNotification, Long> {
    List<FaceNotification> findAllByOrderByRegisteredAtDesc();
    long countByReadFalse();
}
