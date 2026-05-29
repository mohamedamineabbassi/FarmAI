package com.farm.backend.dto;

/** Requête de pointage Face ID : email reconnu par le moteur IA (+ photo optionnelle). */
public class CheckinRequest {

    private String email;
    private String imagePath;

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getImagePath() {
        return imagePath;
    }

    public void setImagePath(String imagePath) {
        this.imagePath = imagePath;
    }
}
