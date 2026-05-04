import { Component, OnInit, OnDestroy, ViewEncapsulation, HostListener } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';

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

  private cursorGlow: HTMLElement | null = null;
  private cursorTrail: HTMLElement | null = null;
  private particles: HTMLElement[] = [];
  private animFrame: number = 0;
  private mouseX = 0;
  private mouseY = 0;
  private glowX = 0;
  private glowY = 0;

  constructor(private http: HttpClient, private router: Router) {}

  ngOnInit() {
    this.createCursorEffects();
    this.animateGlow();
  }

  ngOnDestroy() {
    if (this.cursorGlow) this.cursorGlow.remove();
    if (this.cursorTrail) this.cursorTrail.remove();
    this.particles.forEach(p => p.remove());
    cancelAnimationFrame(this.animFrame);
  }

  // =========================
  // ✨ CURSOR GLOW EFFECT
  // =========================
  private createCursorEffects() {
    // Main glow orb
    this.cursorGlow = document.createElement('div');
    this.cursorGlow.className = 'cursor-glow';
    document.querySelector('.login-wrapper')?.appendChild(this.cursorGlow);

    // Secondary trail (smaller, delayed)
    this.cursorTrail = document.createElement('div');
    this.cursorTrail.className = 'cursor-trail';
    document.querySelector('.login-wrapper')?.appendChild(this.cursorTrail);

    // Floating ambient particles
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
    // Smooth interpolation (easing) for the glow to follow cursor
    this.glowX += (this.mouseX - this.glowX) * 0.08;
    this.glowY += (this.mouseY - this.glowY) * 0.08;

    if (this.cursorGlow) {
      this.cursorGlow.style.left = this.glowX + 'px';
      this.cursorGlow.style.top = this.glowY + 'px';
    }

    // Trail follows even slower
    if (this.cursorTrail) {
      const trailX = this.glowX + (this.mouseX - this.glowX) * 0.3;
      const trailY = this.glowY + (this.mouseY - this.glowY) * 0.3;
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

  // =========================
  // 🔐 LOGIN NORMAL
  // =========================
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

        // ✅ STOCKAGE
        localStorage.setItem('token', res.token);
        localStorage.setItem('role', res.role);
        localStorage.setItem('email', res.email);
        localStorage.setItem('faceRegistered', res.faceRegistered);
        localStorage.setItem('userId', res.userId);

        // =========================
        // 🔥 REDIRECTION PAR ROLE
        // =========================

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
        this.error = err.error?.message || 'Login failed ❌';

      }
    });
  }

  // =========================
  // 🤖 LOGIN PAR VISAGE
  // =========================
  faceLogin() {

    this.faceLoading = true;
    this.error = '';

    this.http.post<any>('http://localhost:8081/api/auth/face-login', {})
      .subscribe({

        next: (res) => {

          this.faceLoading = false;

          console.log("FACE LOGIN:", res);

          if (res.status === 'success') {

            const role = res.role || '';

            // ✅ STOCKAGE
            localStorage.setItem('token', res.token);
            localStorage.setItem('role', role);
            localStorage.setItem('email', res.email);
            localStorage.setItem('faceRegistered', 'true');

            // 🔥 REDIRECTION
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
            this.error = res.message || "Face non reconnue ❌";
          }
        },

        error: () => {
          this.faceLoading = false;
          this.error = "Erreur reconnaissance ❌";
        }
      });
  }
}