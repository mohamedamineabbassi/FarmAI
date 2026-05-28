import { Component, OnInit, OnDestroy, ViewChild, ElementRef, NgZone, ChangeDetectorRef } from '@angular/core';
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

  showCamera = false;
  cameraReady = false;
  faceDetected = false;
  capturing = false;
  capturedImage: string | null = null;
  private mediaStream: MediaStream | null = null;

  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;

  constructor(
    private userService: UserService,
    private faceService: FaceService,
    private http: HttpClient,
    public langService: LanguageService,
    private zone: NgZone,
    private cdr: ChangeDetectorRef
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
      error: () => console.error('Erreur chargement profil')
    });
  }

  checkFaceStatus() {
    this.faceService.getStatus().subscribe({
      next: (res) => this.faceRegistered = res.faceRegistered,
      error: () => console.error('Erreur status visage')
    });
  }

  openCamera() {
    this.showCamera = true;
    this.capturedImage = null;
    this.cameraReady = false;
    this.faceDetected = false;
    this.message = '';
    this.cameraStatus = this.langService.t('Initialisation de la caméra...', 'Initializing camera...');
    setTimeout(() => this.startCamera(), 200);
  }

  private startCamera(): void {
    navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
      audio: false
    })
    .then((stream) => {
      this.zone.run(() => {
        this.mediaStream = stream;
        setTimeout(() => {
          const video = this.videoElement?.nativeElement;
          if (!video) {
            this.cameraStatus = this.langService.t(
              'Élément vidéo introuvable. Rechargez la page.',
              'Video element not found. Reload the page.'
            );
            this.cdr.detectChanges();
            return;
          }
          video.srcObject = stream;
          video.play()
            .then(() => {
              this.zone.run(() => {
                this.cameraReady = true;
                this.cameraStatus = this.langService.t(
                  'Caméra prête — Positionnez votre visage au centre',
                  'Camera ready — Position your face in the center'
                );
                this.cdr.detectChanges();
              });
            })
            .catch(() => {
              this.zone.run(() => {
                this.cameraStatus = this.langService.t(
                  'Impossible de lire le flux vidéo.',
                  'Cannot read video stream.'
                );
                this.cdr.detectChanges();
              });
            });
        }, 100);
      });
    })
    .catch((err: any) => {
      this.zone.run(() => {
        if (err.name === 'NotAllowedError') {
          this.cameraStatus = this.langService.t(
            'Accès caméra refusé. Autorisez dans les paramètres navigateur.',
            'Camera access denied. Allow it in browser settings.'
          );
        } else if (err.name === 'NotFoundError') {
          this.cameraStatus = this.langService.t(
            'Aucune caméra détectée sur cet appareil.',
            'No camera detected on this device.'
          );
        } else if (err.name === 'NotReadableError') {
          this.cameraStatus = this.langService.t(
            'Caméra déjà utilisée par une autre application.',
            'Camera already in use by another application.'
          );
        } else {
          this.cameraStatus = this.langService.t('Erreur caméra : ', 'Camera error: ')
            + (err.message || err.name);
        }
        this.cdr.detectChanges();
      });
    });
  }

  stopCamera() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(t => t.stop());
      this.mediaStream = null;
    }
    if (this.videoElement?.nativeElement) {
      this.videoElement.nativeElement.srcObject = null;
    }
    this.showCamera = false;
    this.cameraReady = false;
    this.faceDetected = false;
    this.capturedImage = null;
    this.capturing = false;
  }

  captureAndRegister() {
    const video = this.videoElement?.nativeElement;
    if (!video || !this.mediaStream) {
      this.cameraStatus = this.langService.t('Caméra non prête.', 'Camera not ready.');
      return;
    }
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      this.cameraStatus = this.langService.t(
        'Caméra encore en chargement, attendez et réessayez.',
        'Camera still loading, wait and try again.'
      );
      return;
    }

    const userId = localStorage.getItem('userId');
    if (!userId) {
      this.cameraStatus = this.langService.t(
        'Session expirée. Reconnectez-vous.',
        'Session expired. Please log in again.'
      );
      return;
    }

    this.capturing = true;
    this.cameraStatus = this.langService.t('Analyse du visage en cours...', 'Analyzing face...');

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')!.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      this.zone.run(() => {
        if (!blob) {
          this.capturing = false;
          this.cameraStatus = this.langService.t(
            'Impossible de capturer l\'image.',
            'Cannot capture image.'
          );
          return;
        }

        const form = new FormData();
        form.append('image', blob, 'face.jpg');
        form.append('userId', userId);

        this.http.post<any>('http://localhost:8081/api/auth/face/register-image', form)
          .subscribe({
            next: (res) => {
              this.capturing = false;
              if (res.status === 'success') {
                this.faceRegistered = true;
                this.stopCamera();
                localStorage.setItem('faceRegistered', 'true');
                this.showMessage(
                  this.langService.t('✅ Visage enregistré avec succès !', '✅ Face saved successfully!'),
                  false
                );
              } else {
                this.cameraStatus = res.message ||
                  this.langService.t('❌ Aucun visage détecté. Réessayez.', '❌ No face detected. Try again.');
              }
            },
            error: (err) => {
              this.capturing = false;
              const msg = err.error?.message || err.error?.error ||
                this.langService.t('Erreur lors de l\'enregistrement du visage', 'Error saving face');
              this.cameraStatus = msg;
              this.showMessage(msg, true);
            }
          });
      });
    }, 'image/jpeg', 0.85);
  }

  retakePhoto() {
    this.capturedImage = null;
    this.cameraStatus = this.langService.t(
      'Caméra active — Positionnez votre visage au centre',
      'Camera active — Position your face in the center'
    );
  }

  onRegisterFace() { this.openCamera(); }
  onUpdateFace()   { this.openCamera(); }

  onDeleteFace() {
    const msg = this.langService.t('Supprimer votre visage enregistré ?', 'Delete your registered face?');
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
      error: () => {
        this.loading = false;
        this.showMessage(
          this.langService.t('Erreur lors de la suppression ❌', 'Error during deletion ❌'),
          true
        );
      }
    });
  }

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
