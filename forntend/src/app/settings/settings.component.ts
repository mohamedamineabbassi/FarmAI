import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { UserService, User } from '../services/user.service';
import { FaceService } from '../services/face.service';
import { LanguageService } from '../services/language.service';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements OnInit, OnDestroy {

  user: User = {
    firstName: '',
    lastName: '',
    email: '',
    phone: ''
  };

  passwords = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  };

  loading = false;
  faceLoading = false;
  faceRegistered = false;
  message = '';
  isError = false;
  cameraStatus = '';

  // Camera preview
  showCamera = false;
  cameraReady = false;
  faceDetected = false;
  capturing = false;
  capturedImage: string | null = null;
  stream: MediaStream | null = null;
  detectionInterval: any = null;

  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement') canvasElement!: ElementRef<HTMLCanvasElement>;

  constructor(
    private userService: UserService,
    private faceService: FaceService,
    private http: HttpClient,
    public langService: LanguageService
  ) { }

  ngOnInit(): void {
    this.user.email = localStorage.getItem('email') || '';
    this.fetchProfile();
    this.checkFaceStatus();
  }

  ngOnDestroy(): void {
    this.stopCamera();
  }

  fetchProfile() {
    this.userService.getProfile().subscribe({
      next: (data) => this.user = data,
      error: () => console.error("Erreur chargement profil")
    });
  }

  checkFaceStatus() {
    this.faceService.getStatus().subscribe({
      next: (res) => this.faceRegistered = res.faceRegistered,
      error: () => console.error("Erreur status visage")
    });
  }

  // =========================
  // 📷 CAMERA MANAGEMENT (Shared Stream)
  // =========================

  openCamera() {
    this.showCamera = true;
    this.capturedImage = null;
    this.cameraReady = true;
    this.faceDetected = false;
    this.message = '';
    this.cameraStatus = this.langService.t(
      'Caméra partagée active — Positionnez votre visage',
      'Shared camera active — Position your face'
    );
  }

  stopCamera() {
    this.showCamera = false;
    this.cameraReady = false;
    this.faceDetected = false;
    this.capturedImage = null;
  }

  // =========================
  // 📸 CAPTURE & REGISTER
  // =========================

  captureAndRegister() {
    this.capturing = true;
    this.cameraStatus = this.langService.t('Analyse du visage en cours...', 'Analyzing face...');

    // 🔥 Passe par le backend Spring Boot (qui appelle lui-même le serveur IA)
    // Cela garantit que faceRegistered est mis à jour en base de données
    const request$ = this.faceRegistered
      ? this.http.put<any>('http://localhost:8081/api/face/update', {})
      : this.http.post<any>('http://localhost:8081/api/face/register', {});

    request$.subscribe({
      next: (res) => {
        this.capturing = false;
        this.faceRegistered = true;
        this.stopCamera();
        localStorage.setItem('faceRegistered', 'true');
        this.showMessage(
          this.langService.t(
            '✅ Visage enregistré avec succès !',
            '✅ Face saved successfully!'
          ),
          false
        );
      },
      error: (err) => {
        this.capturing = false;
        this.capturedImage = null;
        const msg = err.error?.error || err.error?.message || err.error?.detail ||
          this.langService.t('Erreur lors de l\'enregistrement du visage', 'Error saving face');

        // Cas spécial : aucun visage détecté dans le flux caméra
        if (msg.toLowerCase().includes('face') || msg.toLowerCase().includes('visage')) {
          this.cameraStatus = this.langService.t(
            '❌ Aucun visage détecté. Réessayez.',
            '❌ No face detected. Try again.'
          );
        } else {
          this.cameraStatus = msg;
        }
        this.showMessage(msg, true);
      }
    });
  }

  retakePhoto() {
    this.capturedImage = null;
    this.cameraStatus = this.langService.t(
      'Caméra active — Positionnez votre visage au centre',
      'Camera active — Position your face in the center'
    );
  }

  // =========================
  // 🔧 FACE ACTIONS (using camera preview)
  // =========================

  onRegisterFace() {
    this.openCamera();
  }

  onUpdateFace() {
    this.openCamera();
  }

  onDeleteFace() {
    const msg = this.langService.t(
      'Supprimer votre visage enregistré ?',
      'Delete your registered face?'
    );
    if (!confirm(msg)) return;

    this.loading = true;
    this.faceService.deleteFace().subscribe({
      next: () => {
        this.loading = false;
        this.faceRegistered = false;
        localStorage.setItem('faceRegistered', 'false');
        this.showMessage(
          this.langService.t('Visage supprimé avec succès ✅', 'Face deleted successfully ✅'),
          false
        );
      },
      error: (err) => {
        this.loading = false;
        this.showMessage(
          this.langService.t('Erreur lors de la suppression ❌', 'Error during deletion ❌'),
          true
        );
      }
    });
  }

  // =========================
  // 👤 PROFILE & PASSWORD
  // =========================

  updateProfile() {
    this.loading = true;
    this.userService.updateProfile(this.user).subscribe({
      next: () => {
        this.loading = false;
        this.showMessage(
          this.langService.t('Profil mis à jour avec succès ✅', 'Profile updated successfully ✅'),
          false
        );
      },
      error: () => {
        this.loading = false;
        this.showMessage(
          this.langService.t('Erreur lors de la mise à jour ❌', 'Error updating profile ❌'),
          true
        );
      }
    });
  }

  changePassword() {
    if (this.passwords.newPassword !== this.passwords.confirmPassword) {
      this.showMessage(
        this.langService.t('Les mots de passe ne correspondent pas ❌', 'Passwords do not match ❌'),
        true
      );
      return;
    }

    this.loading = true;
    this.userService.changePassword(this.passwords).subscribe({
      next: () => {
        this.loading = false;
        this.showMessage(
          this.langService.t('Mot de passe mis à jour ✅', 'Password updated ✅'),
          false
        );
        this.passwords = { oldPassword: '', newPassword: '', confirmPassword: '' };
      },
      error: () => {
        this.loading = false;
        this.showMessage(
          this.langService.t('Erreur lors de la mise à jour du mot de passe ❌', 'Error updating password ❌'),
          true
        );
      }
    });
  }

  private showMessage(msg: string, isError: boolean) {
    this.message = msg;
    this.isError = isError;
    setTimeout(() => this.message = '', 5000);
  }
}
