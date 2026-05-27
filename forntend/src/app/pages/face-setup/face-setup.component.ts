import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-face-setup',
  templateUrl: './face-setup.component.html',
  styleUrls: ['./face-setup.component.scss']
})
export class FaceSetupComponent implements OnInit, OnDestroy {

  loading = false;
  error = '';
  success = '';
  cameraReady = false;
  cameraError = '';

  @ViewChild('videoEl', { static: false }) videoEl!: ElementRef<HTMLVideoElement>;
  private mediaStream: MediaStream | null = null;

  constructor(private router: Router, private http: HttpClient) {}

  ngOnInit(): void {
    const userId = localStorage.getItem('userId');
    if (!userId) {
      this.error = 'Identifiant utilisateur introuvable. Veuillez vous reconnecter.';
      return;
    }
    this.startCamera();
  }

  ngOnDestroy(): void {
    this.stopCamera();
  }

  async startCamera(): Promise<void> {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
        audio: false
      });

      // Attendre que le DOM soit prêt
      await new Promise(resolve => setTimeout(resolve, 150));

      if (this.videoEl?.nativeElement) {
        this.videoEl.nativeElement.srcObject = this.mediaStream;
        await this.videoEl.nativeElement.play();
        this.cameraReady = true;
      } else {
        // Retry after Angular renders
        await new Promise(resolve => setTimeout(resolve, 300));
        if (this.videoEl?.nativeElement) {
          this.videoEl.nativeElement.srcObject = this.mediaStream;
          await this.videoEl.nativeElement.play();
          this.cameraReady = true;
        }
      }
    } catch (err: any) {
      console.error('getUserMedia error:', err);
      if (err.name === 'NotAllowedError') {
        this.cameraError = 'Accès à la caméra refusé. Autorisez-le dans les paramètres du navigateur.';
      } else if (err.name === 'NotFoundError') {
        this.cameraError = 'Aucune caméra détectée sur cet appareil.';
      } else if (err.name === 'NotReadableError') {
        this.cameraError = 'Caméra déjà utilisée par une autre application.';
      } else {
        this.cameraError = 'Impossible d\'accéder à la caméra : ' + (err.message || err.name);
      }
    }
  }

  stopCamera(): void {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(t => t.stop());
      this.mediaStream = null;
    }
    if (this.videoEl?.nativeElement) {
      this.videoEl.nativeElement.srcObject = null;
    }
  }

  scanFace(): void {
    if (!this.videoEl?.nativeElement || !this.mediaStream) {
      this.error = 'Caméra non initialisée. Rechargez la page.';
      return;
    }

    const video = this.videoEl.nativeElement;
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      this.error = 'Caméra encore en chargement, veuillez réessayer.';
      return;
    }

    const userIdStr = localStorage.getItem('userId');
    if (!userIdStr) {
      this.error = 'Identifiant utilisateur introuvable. Veuillez vous reconnecter.';
      return;
    }

    this.loading = true;
    this.error = '';
    this.success = '';

    // Capture un snapshot depuis la vidéo en direct
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      this.loading = false;
      this.error = 'Erreur de capture (canvas non disponible).';
      return;
    }
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (!blob) {
        this.loading = false;
        this.error = 'Impossible de capturer l\'image.';
        return;
      }

      const formData = new FormData();
      formData.append('image', blob, 'face.jpg');
      formData.append('userId', userIdStr);

      this.http.post<any>('http://localhost:8081/api/auth/face/register-image', formData)
        .subscribe({
          next: (res) => {
            this.loading = false;

            if (res.status === 'success') {
              this.success = 'Visage enregistré avec succès !';
              localStorage.setItem('faceRegistered', 'true');
              this.stopCamera();

              setTimeout(() => {
                const role = localStorage.getItem('role');
                if (role === 'ROLE_MANAGER') {
                  this.router.navigate(['/dashboard/manager']);
                } else if (role === 'ROLE_VIEWER') {
                  this.router.navigate(['/dashboard/viewer']);
                } else if (role === 'ROLE_ADMIN') {
                  this.router.navigate(['/dashboard']);
                } else {
                  this.router.navigate(['/login']);
                }
              }, 1500);
            } else {
              this.error = res.message || 'Erreur lors de l\'enregistrement du visage.';
            }
          },
          error: (err) => {
            this.loading = false;
            this.error = err.error?.message || err.error?.error || 'Erreur de connexion au serveur IA.';
          }
        });
    }, 'image/jpeg', 0.85);
  }
}
