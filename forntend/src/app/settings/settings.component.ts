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
    this.cameraStatus = this.langService.t('Capture en cours...', 'Capturing...');

    // We no longer capture locally. We ask the AI server to use its latest frame.
    const email = localStorage.getItem('email') || this.user.email;
    this.cameraStatus = this.langService.t(
      'Analyse du visage en cours...',
      'Analyzing face...'
    );

    this.http.post<any>('http://localhost:8000/api/face/register-latest-frame', {
      email: email
    }).subscribe({
      next: (res) => {
        this.capturing = false;

        if (res.status === 'success') {
          this.faceRegistered = true;
          this.stopCamera();
          this.showMessage(
            this.langService.t(
              '✅ Visage enregistré avec succès ! Confiance: ' + Math.round((res.confidence || 0.95) * 100) + '%',
              '✅ Face saved successfully! Confidence: ' + Math.round((res.confidence || 0.95) * 100) + '%'
            ),
            false
          );
          // Also update localStorage
          localStorage.setItem('faceRegistered', 'true');
        } else if (res.status === 'no_face') {
          this.capturedImage = null;
          this.cameraStatus = this.langService.t(
            '❌ Aucun visage détecté. Réessayez.',
            '❌ No face detected. Try again.'
          );
          this.showMessage(
            this.langService.t(
              'Aucun visage détecté. Assurez-vous que votre visage est bien visible.',
              'No face detected. Make sure your face is clearly visible.'
            ),
            true
          );
        } else {
          this.capturedImage = null;
          this.cameraStatus = res.message || 'Error';
          this.showMessage(res.message || 'Error', true);
        }
      },
      error: (err) => {
        this.capturing = false;
        this.capturedImage = null;
        const msg = err.error?.message || err.error?.detail ||
          this.langService.t('Erreur de connexion au serveur IA', 'Error connecting to AI server');
        this.cameraStatus = msg;
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
          true
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
