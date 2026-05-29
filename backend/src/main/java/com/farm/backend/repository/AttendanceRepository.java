package com.farm.backend.repository;

import com.farm.backend.entity.AttendanceRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AttendanceRepository extends JpaRepository<AttendanceRecord, Long> {

    List<AttendanceRecord> findAllByOrderByTimestampDesc();

    List<AttendanceRecord> findByEmployeeNameContainingIgnoreCaseOrderByTimestampDesc(String name);

    /** Dernier enregistrement de présence d'une personne (pour le protocole de pointage entrée/sortie). */
    AttendanceRecord findFirstByEmployeeNameOrderByTimestampDesc(String employeeName);
}
