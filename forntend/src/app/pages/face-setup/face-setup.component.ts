import { Component, OnInit, AfterViewInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { timeout } from 'rxjs/operators';

@Component({
  selector: 'app-face-setup',
  templateUrl: './face-setup.component.html',
  styleUrls: ['./face-setup.component.scss']
})
export class FaceSetupComponent implements OnInit, AfterViewInit, OnDestroy {

  loading = false;
  error = '';
  success = '';
  cameraReady = false;
  cameraError = '';
  scanStatus = '';   // Message de progression pendant le scan

  @ViewChild('videoEl', { static: false }) videoEl!: ElementRef<HTMLVideoElement>;
  private mediaStream: MediaStream | null = null;

  constructor(private router: Router, private http: HttpClient) {}

  ngOnInit(): void {
    const userId = localStorage.getItem('userId');
    if (!userId) {
      this.error = 'Identifiant utilisateur introuvable. Veuillez vous reconnecter.';
    }
  }

  // ✅ ngAfterViewInit : le <video #videoEl> existe dans le DOM maintenant
  ngAfterViewInit(): void {
    if (!this.error) {
      this.startCamera();
    }
  }

  ngOnDestroy(): void {
    this.stopCamera();
  }

  async startCamera(): Promise<void> {
    this.cameraError = '';
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
        audio: false
      });

      if (this.videoEl?.nativeElement) {
        this.videoEl.nativeElement.srcObject = this.mediaStream;
        await this.videoEl.nativeElement.play();
        this.cameraReady = true;
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
      this.error = 'Caméra encore en chargement, veuillez réessayer dans 2 secondes.';
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
    this.scanStatus = 'Capture de l\'image...';

    // Capture snapshot depuis le flux vidéo
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
        this.scanStatus = '';
        this.error = 'Impossible de capturer l\'image.';
        return;
      }

      this.scanStatus = 'Envoi au moteur IA...';

      const formData = new FormData();
      formData.append('image', blob, 'face.jpg');
      formData.append('userId', userIdStr);

      this.http.post<any>('http://localhost:8081/api/auth/face/register-image', formData)
        .pipe(timeout(25000))   // ✅ Timeout 25 secondes max
        .subscribe({
          next: (res) => {
            this.loading = false;
            this.scanStatus = '';

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
              this.error = res.message || 'Visage non détecté. Rapprochez-vous de la caméra.';
            }
          },
          error: (err) => {
            this.loading = false;
            this.scanStatus = '';
            if (err.name === 'TimeoutError' || err.constructor?.name === 'TimeoutError') {
              this.error = 'Délai dépassé (25s). Vérifiez que le serveur IA (port 8000) est démarré.';
            } else {
              this.error = err.error?.message || err.error?.error || 'Erreur de connexion au serveur IA.';
            }
          }
        });
    }, 'image/jpeg', 0.85);
  }
}
