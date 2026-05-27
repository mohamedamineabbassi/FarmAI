import {
  Component, OnInit, AfterViewInit, OnDestroy,
  ViewChild, ElementRef, NgZone, ChangeDetectorRef
} from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { timeout } from 'rxjs/operators';

@Component({
  selector: 'app-face-setup',
  templateUrl: './face-setup.component.html',
  styleUrls: ['./face-setup.component.scss']
})
export class FaceSetupComponent implements OnInit, AfterViewInit, OnDestroy {

  loading    = false;
  error      = '';
  success    = '';
  cameraReady = false;
  cameraError = '';
  scanStatus  = '';

  @ViewChild('videoEl', { static: false }) videoEl!: ElementRef<HTMLVideoElement>;
  private mediaStream: MediaStream | null = null;

  constructor(
    private router : Router,
    private http   : HttpClient,
    private zone   : NgZone,
    private cdr    : ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    if (!localStorage.getItem('userId')) {
      this.error = 'Identifiant utilisateur introuvable. Veuillez vous reconnecter.';
    }
  }

  ngAfterViewInit(): void {
    if (!this.error) {
      // Petit délai pour laisser Angular finir le rendu du <video>
      setTimeout(() => this.startCamera(), 200);
    }
  }

  ngOnDestroy(): void {
    this.stopStream();
  }

  // ─────────────────────────────────────────────
  // CAMÉRA
  // ─────────────────────────────────────────────

  startCamera(): void {
    this.cameraError = '';
    this.cameraReady = false;

    navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
      audio: false
    })
    .then((stream) => {
      // ✅ zone.run() → Angular détecte les changements après l'appel async
      this.zone.run(() => {
        this.mediaStream = stream;

        // Attendre un tick pour que Angular rende le <video> avec le nouveau state
        setTimeout(() => {
          const video = this.videoEl?.nativeElement;
          if (!video) {
            this.cameraError = 'Élément vidéo introuvable. Rechargez la page.';
            this.cdr.detectChanges();
            return;
          }

          video.srcObject = stream;
          video.play()
            .then(() => {
              this.zone.run(() => {
                this.cameraReady = true;
                this.cdr.detectChanges();
              });
            })
            .catch((playErr) => {
              this.zone.run(() => {
                this.cameraError = 'Impossible de lire le flux vidéo : ' + playErr.message;
                this.cdr.detectChanges();
              });
            });
        }, 100);
      });
    })
    .catch((err) => {
      this.zone.run(() => {
        if (err.name === 'NotAllowedError') {
          this.cameraError = 'Accès à la caméra refusé. Cliquez sur l\'icône 🔒 dans la barre d\'adresse et autorisez la caméra.';
        } else if (err.name === 'NotFoundError') {
          this.cameraError = 'Aucune caméra détectée sur cet appareil.';
        } else if (err.name === 'NotReadableError') {
          this.cameraError = 'Caméra déjà utilisée par une autre application. Fermez-la et réessayez.';
        } else {
          this.cameraError = 'Erreur caméra : ' + (err.message || err.name);
        }
        this.cdr.detectChanges();
      });
    });
  }

  private stopStream(): void {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(t => t.stop());
      this.mediaStream = null;
    }
    if (this.videoEl?.nativeElement) {
      this.videoEl.nativeElement.srcObject = null;
    }
  }

  // ─────────────────────────────────────────────
  // SCAN
  // ─────────────────────────────────────────────

  scanFace(): void {
    const video = this.videoEl?.nativeElement;

    if (!video || !this.mediaStream) {
      this.error = 'Caméra non prête. Rechargez la page.';
      return;
    }
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      this.error = 'Caméra encore en chargement, attendez 2 secondes et réessayez.';
      return;
    }

    const userIdStr = localStorage.getItem('userId');
    if (!userIdStr) {
      this.error = 'Session expirée. Veuillez vous reconnecter.';
      return;
    }

    this.loading    = true;
    this.error      = '';
    this.success    = '';
    this.scanStatus = 'Capture de l\'image...';

    // ── Capture snapshot ──
    const canvas = document.createElement('canvas');
    canvas.width  = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d')!;
    ctx.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      if (!blob) {
        this.loading    = false;
        this.scanStatus = '';
        this.error      = 'Impossible de capturer l\'image.';
        return;
      }

      this.scanStatus = 'Envoi au moteur IA (max 25s)...';

      const form = new FormData();
      form.append('image', blob, 'face.jpg');
      form.append('userId', userIdStr);

      this.http.post<any>('http://localhost:8081/api/auth/face/register-image', form)
        .pipe(timeout(25000))
        .subscribe({
          next: (res) => {
            this.loading    = false;
            this.scanStatus = '';

            if (res.status === 'success') {
              this.success = 'Visage enregistré avec succès !';
              localStorage.setItem('faceRegistered', 'true');
              this.stopStream();

              setTimeout(() => {
                const role = localStorage.getItem('role');
                if      (role === 'ROLE_MANAGER') this.router.navigate(['/dashboard/manager']);
                else if (role === 'ROLE_VIEWER')  this.router.navigate(['/dashboard/viewer']);
                else if (role === 'ROLE_ADMIN')   this.router.navigate(['/dashboard']);
                else                              this.router.navigate(['/login']);
              }, 1500);

            } else {
              this.error = res.message || 'Aucun visage détecté. Rapprochez-vous de la caméra et réessayez.';
            }
          },
          error: (err) => {
            this.loading    = false;
            this.scanStatus = '';

            if (err.name === 'TimeoutError' || err.constructor?.name === 'TimeoutError') {
              this.error = '⏱ Délai dépassé (25s). Vérifiez que le serveur IA est démarré sur le port 8000.';
            } else {
              this.error = err.error?.message || err.error?.error || 'Erreur de connexion au serveur.';
            }
          }
        });
    }, 'image/jpeg', 0.85);
  }
}
