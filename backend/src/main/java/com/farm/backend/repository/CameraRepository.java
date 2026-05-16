package com.farm.backend.repository;

import com.farm.backend.entity.CameraEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.repository.query.Param;
import org.springframework.transaction.annotation.Transactional;

public interface CameraRepository extends JpaRepository<CameraEntity, Long> {
    List<CameraEntity> findByDepartmentId(Long departmentId);

    @Modifying
    @Transactional
    @Query(value = "DELETE FROM camera_events WHERE camera_id = :cameraId", nativeQuery = true)
    void deleteCameraEvents(@Param("cameraId") Long cameraId);

    @Modifying
    @Transactional
    @Query(value = "DELETE FROM camera_alerts WHERE camera_id = :cameraId", nativeQuery = true)
    void deleteCameraAlerts(@Param("cameraId") Long cameraId);

    @Modifying
    @Transactional
    @Query(value = "DELETE FROM face_events WHERE camera_id = :cameraId", nativeQuery = true)
    void deleteFaceEvents(@Param("cameraId") Long cameraId);

    @Modifying
    @Transactional
    @Query(value = "DELETE FROM role_events WHERE camera_id = :cameraId", nativeQuery = true)
    void deleteRoleEvents(@Param("cameraId") Long cameraId);

    @Modifying
    @Transactional
    @Query(value = "DELETE FROM unknown_detections WHERE camera_id = :cameraId", nativeQuery = true)
    void deleteUnknownDetections(@Param("cameraId") Long cameraId);
}
