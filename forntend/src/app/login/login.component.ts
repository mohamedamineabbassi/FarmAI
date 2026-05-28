import { Component, OnInit, OnDestroy, ViewEncapsulation, HostListener, ViewChild, ElementRef, NgZone } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { LanguageService } from '../services/language.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class LoginComponent implements OnInit, OnDestroy {

  email: string = '';
  password: string = '';

  loading = false;
  faceLoading = false;

  error = '';
  success = '';

  showCamera = false;
  cameraStatus = '';

  @ViewChild('videoEl', { static: false }) videoEl!: ElementRef<HTMLVideoElement>;
  private mediaStream: MediaStream | null = null;

  private cursorGlow: HTMLElement | null = null;
  private cursorTrail: HTMLElement | null = null;
  private particles: HTMLElement[] = [];
  private animFrame: number = 0;
  private mouseX = 0;
  private mouseY = 0;
  private glowX = 0;
  private glowY = 0;

  constructor(
    private http: HttpClient,
    private router: Router,
    private route: ActivatedRoute,
    private zone: NgZone,
    public langService: LanguageService
  ) {}

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      if (params['sessionExpired'] === 'true') {
        this.error = '⏱️ Votre session a expiré. Veuillez vous reconnecter.';
      }
    });
    this.createCursorEffects();
    this.animateGlow();
  }

  ngOnDestroy() {
    if (this.cursorGlow) this.cursorGlow.remove();
    if (this.cursorTrail) this.cursorTrail.remove();
    this.particles.forEach(p => p.remove());
    cancelAnimationFrame(this.animFrame);

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(t => t.stop());
      this.mediaStream = null;
    }
  }

  private createCursorEffects() {
    this.cursorGlow = document.createElement('div');
    this.cursorGlow.className = 'cursor-glow';
    document.querySelector('.login-wrapper')?.appendChild(this.cursorGlow);

    this.cursorTrail = document.createElement('div');
    this.cursorTrail.className = 'cursor-trail';
    document.querySelector('.login-wrapper')?.appendChild(this.cursorTrail);

    const wrapper = document.querySelector('.login-wrapper');
    if (wrapper) {
      for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.className = 'ambient-particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.width = (Math.random() * 3 + 1) + 'px';
        particle.style.height = particle.style.width;
        particle.style.animationDelay = (Math.random() * 8) + 's';
        particle.style.animationDuration = (Math.random() * 6 + 6) + 's';
        particle.style.opacity = (Math.random() * 0.4 + 0.1).toString();
        wrapper.appendChild(particle);
        this.particles.push(particle);
      }
    }
  }

  private animateGlow() {
    this.glowX += (this.mouseX - this.glowX) * 0.08;
    this.glowY += (this.mouseY - this.glowY) * 0.08;

    if (this.cursorGlow) {
      this.cursorGlow.style.left = this.glowX + 'px';
      this.cursorGlow.style.top = this.glowY + 'px';
    }

    if (this.cursorTrail) {
      this.cursorTrail.style.left = (this.glowX - (this.mouseX - this.glowX) * 0.5) + 'px';
      this.cursorTrail.style.top = (this.glowY - (this.mouseY - this.glowY) * 0.5) + 'px';
    }

    this.animFrame = requestAnimationFrame(() => this.animateGlow());
  }

  @HostListener('document:mousemove', ['$event'])
  onMouseMove(e: MouseEvent) {
    this.mouseX = e.clientX;
    this.mouseY = e.clientY;
  }

  login() {

    this.loading = true;
    this.error = '';

    this.http.post<any>('http://localhost:8081/api/auth/login', {
      email: this.email,
      password: this.password
    }).subscribe({

      next: (res) => {

        this.loading = false;

        console.log("LOGIN RESPONSE:", res);

        localStorage.setItem('token', res.token);
        localStorage.setItem('role', res.role);
        localStorage.setItem('email', res.email);
        localStorage.setItem('faceRegistered', res.faceRegistered);
        localStorage.setItem('userId', res.userId);

        if (res.role === 'ROLE_ADMIN') {

          this.router.navigate(['/dashboard']);

        } else if (res.role === 'ROLE_MANAGER' || res.role === 'ROLE_VIEWER') {

          if (res.faceRegistered === false || res.faceRegistered === 'false') {
            this.router.navigate(['/face-setup']);
          } else {
            const path = res.role === 'ROLE_MANAGER' ? '/dashboard/manager' : '/dashboard/viewer';
            this.router.navigate([path]);
          }

        } else {
          this.router.navigate(['/login']);
        }
      },

      error: (err) => {
        this.loading = false;
        this.error = err.error?.message || err.error?.error || 'Email ou mot de passe incorrect ❌';
      }
    });
  }

  async openCamera() {
    this.error = '';
    this.showCamera = true;
    this.cameraStatus = this.langService.t(
      'Initialisation de la caméra...',
      'Initializing camera...'
    );

    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width:  { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        },
        audio: false
      });

      await new Promise(resolve => setTimeout(resolve, 50));

      if (this.videoEl && this.videoEl.nativeElement) {
        this.videoEl.nativeElement.srcObject = this.mediaStream;
        await this.videoEl.nativeElement.play();
        this.cameraStatus = this.langService.t(
          'Caméra prête — Cliquez sur SCANNER',
          'Camera ready — Click SCAN'
        );
      } else {
        throw new Error('Video element not ready');
      }
    } catch (err: any) {
      console.error('getUserMedia error:', err);
      this.showCamera = false;
      if (err.name === 'NotAllowedError') {
        this.error = this.langService.t(
          'Accès à la caméra refusé. Autorisez-le dans les paramètres du navigateur.',
          'Camera access denied. Allow it in your browser settings.'
        );
      } else if (err.name === 'NotFoundError') {
        this.error = this.langService.t(
          'Aucune caméra détectée sur cet appareil.',
          'No camera detected on this device.'
        );
      } else if (err.name === 'NotReadableError') {
        this.error = this.langService.t(
          'Caméra déjà utilisée par une autre application.',
          'Camera is already in use by another application.'
        );
      } else {
        this.error = this.langService.t(
          'Impossible d\'accéder à la caméra : ',
          'Cannot access camera: '
        ) + (err.message || err.name);
      }
    }
  }

  stopCamera() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(t => t.stop());
      this.mediaStream = null;
    }
    if (this.videoEl && this.videoEl.nativeElement) {
      this.videoEl.nativeElement.srcObject = null;
    }
    this.showCamera = false;
    this.faceLoading = false;
  }

  faceLogin() {
    if (!this.videoEl || !this.videoEl.nativeElement || !this.mediaStream) {
      this.error = 'Caméra non initialisée';
      return;
    }

    const video = this.videoEl.nativeElement;
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      this.cameraStatus = this.langService.t(
        'Caméra encore en cours de chargement, réessayez...',
        'Camera still loading, try again...'
      );
      return;
    }

    this.faceLoading = true;
    this.error = '';
    this.cameraStatus = this.langService.t('Analyse en cours...', 'Analyzing...');

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      this.faceLoading = false;
      this.error = 'Canvas non disponible';
      return;
    }
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      this.zone.run(() => {
        if (!blob) {
          this.faceLoading = false;
          this.error = 'Impossible de capturer l\'image';
          return;
        }

        const formData = new FormData();
        formData.append('image', blob, 'face.jpg');

        this.http.post<any>('http://localhost:8081/api/auth/face-login', formData)
          .subscribe({
            next: (res) => {
              this.faceLoading = false;

              if (res.status === 'success') {
                const role = res.role || '';

                localStorage.setItem('token', res.token);
                localStorage.setItem('role', role);
                localStorage.setItem('email', res.email);
                localStorage.setItem('faceRegistered', 'true');
                if (res.userId) localStorage.setItem('userId', res.userId);

                this.stopCamera();

                if (role === 'ROLE_ADMIN' || role === 'ADMIN') {
                  this.router.navigate(['/dashboard']);
                } else if (role === 'ROLE_MANAGER' || role === 'MANAGER') {
                  this.router.navigate(['/dashboard/manager']);
                } else if (role === 'ROLE_VIEWER' || role === 'VIEWER') {
                  this.router.navigate(['/dashboard/viewer']);
                } else {
                  this.router.navigate(['/login']);
                }
              } else {
                this.error = res.message || 'Visage non reconnu ❌';
                this.cameraStatus = this.error;
              }
            },
            error: (err) => {
              this.faceLoading = false;
              this.error = err.error?.message || 'Erreur reconnaissance ❌';
              this.cameraStatus = this.error;
            }
          });
      });
    }, 'image/jpeg', 0.85);
  }
}
