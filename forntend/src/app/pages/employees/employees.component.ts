import { Component, OnInit, OnDestroy, ViewChild, ElementRef, NgZone, ChangeDetectorRef } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { EmployeeService, Employee } from '../../services/employee.service';
import { timeout } from 'rxjs/operators';

@Component({
  selector: 'app-employees',
  templateUrl: './employees.component.html',
  styleUrls: ['./employees.component.scss']
})
export class EmployeesComponent implements OnInit, OnDestroy {

  employees: Employee[] = [];
  jobs = [
    { value: 'DOCTOR',      label: 'Vétérinaire' },
    { value: 'ELECTRICIAN', label: 'Technicien Électrique' },
    { value: 'WORKER',      label: 'Ouvrier Agricole' }
  ];

  form: any = { name: '', email: '', phone: '', job: '', department: null };
  submitted = false;

  showToast    = false;
  toastMessage = '';
  toastType: 'success' | 'error' = 'success';
  private toastTimer: any;

  isDarkMode = true;

  private readonly emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  // ── Camera modal ──────────────────────────────────────────────
  showCameraModal  = false;
  activeEmployee: Employee | null = null;
  cameraReady      = false;
  cameraError      = '';
  scanLoading      = false;
  scanStatus       = '';
  scanSuccess      = '';
  scanError        = '';

  @ViewChild('captureVideo', { static: false }) captureVideo!: ElementRef<HTMLVideoElement>;
  private mediaStream: MediaStream | null = null;

  constructor(
    private service: EmployeeService,
    private http: HttpClient,
    private zone: NgZone,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit(): void {
    this.applyTheme();
    this.load();
  }

  ngOnDestroy(): void {
    this.stopStream();
  }

  load() {
    this.service.getEmployees().subscribe({
      next: res => this.employees = res,
      error: () => this.toast('Erreur lors du chargement.', 'error')
    });
  }

  get nameValid():  boolean { return this.form.name?.trim().length > 0; }
  get emailValid(): boolean { return !this.form.email || this.emailRegex.test(this.form.email); }
  get formValid():  boolean { return this.nameValid && this.emailValid && !!this.form.job; }

  save() {
    this.submitted = true;
    if (!this.formValid) return;

    const payload: Employee = {
      name:          this.form.name.trim(),
      email:         this.form.email || '',
      phone:         this.form.phone || '',
      job:           this.form.job,
      status:        'PENDING',
      faceRegistered: false
    };

    this.service.create(payload).subscribe({
      next: () => {
        this.toast('Employé ajouté avec succès ✅', 'success');
        this.load();
        this.form = { name: '', email: '', phone: '', job: '', department: null };
        this.submitted = false;
      },
      error: () => this.toast("Erreur lors de l'ajout.", 'error')
    });
  }

  delete(id?: number) {
    if (!id) return;
    if (!confirm('Supprimer cet employé ?')) return;
    this.service.delete(id).subscribe({
      next: () => { this.toast('Employé supprimé.', 'success'); this.load(); },
      error: () => this.toast('Erreur lors de la suppression.', 'error')
    });
  }

  approve(id?: number) {
    if (!id) return;
    this.service.approve(id).subscribe({
      next: () => { this.toast('Employé approuvé ✅', 'success'); this.load(); },
      error: () => this.toast("Erreur lors de l'approbation.", 'error')
    });
  }

  validateFace(id?: number) {
    if (!id) return;
    this.service.validateFace(id).subscribe({
      next: () => { this.toast('Visage validé ✅', 'success'); this.load(); },
      error: () => this.toast('Erreur lors de la validation.', 'error')
    });
  }

  // ── Camera modal ──────────────────────────────────────────────

  captureFace(employee: Employee) {
    this.activeEmployee = employee;
    this.cameraReady    = false;
    this.cameraError    = '';
    this.scanLoading    = false;
    this.scanStatus     = '';
    this.scanSuccess    = '';
    this.scanError      = '';
    this.showCameraModal = true;
    setTimeout(() => this.startCamera(), 250);
  }

  startCamera() {
    this.cameraError = '';
    this.cameraReady = false;

    navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
      audio: false
    })
    .then((stream) => {
      this.zone.run(() => {
        this.mediaStream = stream;
        setTimeout(() => {
          const video = this.captureVideo?.nativeElement;
          if (!video) {
            this.scanStatus = 'Élément vidéo introuvable.';
            this.cdr.detectChanges();
            return;
          }
          video.srcObject = stream;
          video.play()
            .then(() => this.zone.run(() => { this.cameraReady = true; this.scanStatus = 'Caméra prête — Appuyez pour capturer'; this.cdr.detectChanges(); }))
            .catch(() => this.zone.run(() => { this.scanStatus = 'Impossible de lire le flux vidéo.'; this.cdr.detectChanges(); }));
        }, 100);
      });
    })
    .catch((err: any) => {
      this.zone.run(() => {
        if (err.name === 'NotAllowedError')   this.scanStatus = 'Accès caméra refusé. Autorisez dans le navigateur.';
        else if (err.name === 'NotFoundError') this.scanStatus = 'Aucune caméra détectée.';
        else if (err.name === 'NotReadableError') this.scanStatus = 'Caméra déjà utilisée par une autre application.';
        else this.scanStatus = 'Erreur caméra : ' + (err.message || err.name);
        this.cdr.detectChanges();
      });
    });
  }

  stopStream() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(t => t.stop());
      this.mediaStream = null;
    }
    if (this.captureVideo?.nativeElement) {
      this.captureVideo.nativeElement.srcObject = null;
    }
  }

  closeModal() {
    this.stopStream();
    this.showCameraModal = false;
    this.activeEmployee  = null;
    if (this.scanSuccess) this.load();
  }

  onOverlayClick(event: MouseEvent) {
    if (event.target === event.currentTarget) this.closeModal();
  }

  doScan() {
    if (!this.activeEmployee?.id) return;
    const video = this.captureVideo?.nativeElement;
    if (!video || !this.mediaStream || video.videoWidth === 0) {
      this.scanError = 'Caméra non prête. Attendez et réessayez.';
      return;
    }

    this.scanLoading = true;
    this.scanError   = '';
    this.scanSuccess = '';
    this.scanStatus  = 'Capture de l\'image...';

    const canvas = document.createElement('canvas');
    canvas.width  = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')!.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      this.zone.run(() => {
        if (!blob) {
          this.scanLoading = false;
          this.scanStatus  = '';
          this.scanError   = 'Impossible de capturer l\'image.';
          return;
        }

        this.scanStatus = 'Analyse IA en cours...';
        const form = new FormData();
        form.append('image', blob, 'face.jpg');

        this.http.post<any>(
          `http://localhost:8081/api/employees/register-face-image/${this.activeEmployee!.id}`,
          form
        )
        .pipe(timeout(25000))
        .subscribe({
          next: (res) => {
            this.scanLoading = false;
            this.scanStatus  = '';
            if (res.status === 'success') {
              this.scanSuccess = `✅ Visage de ${res.employeeName || this.activeEmployee!.name} enregistré !`;
              this.stopStream();
              const emp = this.employees.find(e => e.id === this.activeEmployee!.id);
              if (emp) emp.faceRegistered = true;
              setTimeout(() => this.closeModal(), 1500);
            } else {
              this.scanError = res.message || 'Aucun visage détecté. Regardez directement la caméra.';
            }
          },
          error: (err) => {
            this.scanLoading = false;
            this.scanStatus  = '';
            if (err.name === 'TimeoutError' || err.constructor?.name === 'TimeoutError') {
              this.scanError = '⏱ Délai dépassé (25s). Vérifiez que le serveur IA est démarré (port 8000).';
            } else {
              this.scanError = err.error?.message || err.error?.error || 'Erreur serveur.';
            }
          }
        });
      });
    }, 'image/jpeg', 0.85);
  }

  // ── Theme & Toast ──────────────────────────────────────────────

  toggleDarkMode() {
    this.isDarkMode = !this.isDarkMode;
    this.applyTheme();
  }

  private applyTheme() {
    if (this.isDarkMode) document.body.classList.remove('light-mode');
    else document.body.classList.add('light-mode');
  }

  private toast(message: string, type: 'success' | 'error') {
    clearTimeout(this.toastTimer);
    this.toastMessage = message;
    this.toastType    = type;
    this.showToast    = true;
    this.toastTimer = setTimeout(() => this.showToast = false, 3000);
  }
}
