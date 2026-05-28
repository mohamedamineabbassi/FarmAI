import {
  Component, OnInit, AfterViewInit, OnDestroy,
  ViewChild, ElementRef, NgZone, ChangeDetectorRef
} from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { EmployeeService, Employee } from '../services/employee.service';
import { timeout } from 'rxjs/operators';

@Component({
  selector: 'app-viewer-dashboard',
  templateUrl: './viewer-dashboard.component.html'
})
export class ViewerDashboardComponent implements OnInit, AfterViewInit, OnDestroy {

  employees: Employee[]  = [];
  loading                = false;
  searchQuery            = '';
  currentView: 'dashboard' | 'employees' | 'settings' = 'dashboard';

  showCreateForm  = false;
  createLoading   = false;
  createError     = '';
  createSuccess   = '';
  newEmployee = { name: '', email: '', phone: '', job: 'WORKER' };

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
    private http: HttpClient,
    private router: Router,
    private employeeService: EmployeeService,
    private zone: NgZone,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void { this.loadData(); }

  ngAfterViewInit(): void {}

  ngOnDestroy(): void { this.stopStream(); }

  loadData() {
    this.loading = true;
    this.employeeService.getEmployees().subscribe({
      next: (data) => { this.employees = data; this.loading = false; },
      error: () => { this.loading = false; }
    });
  }

  filteredEmployees() {
    if (!this.searchQuery) return this.employees;
    const q = this.searchQuery.toLowerCase();
    return this.employees.filter(e =>
      e.name.toLowerCase().includes(q) ||
      (e.email && e.email.toLowerCase().includes(q)) ||
      e.job.toLowerCase().includes(q)
    );
  }

  getRegisteredCount()   { return this.employees.filter(e => e.faceRegistered).length; }
  getUnregisteredCount() { return this.employees.filter(e => !e.faceRegistered).length; }

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
            this.cameraError = 'Élément vidéo introuvable. Fermez et réessayez.';
            this.cdr.detectChanges();
            return;
          }
          video.srcObject = stream;
          video.play()
            .then(() => this.zone.run(() => { this.cameraReady = true; this.cdr.detectChanges(); }))
            .catch((e: any) => this.zone.run(() => {
              this.cameraError = 'Impossible de lire le flux vidéo.';
              this.cdr.detectChanges();
            }));
        }, 100);
      });
    })
    .catch((err: any) => {
      this.zone.run(() => {
        if (err.name === 'NotAllowedError')   this.cameraError = 'Accès caméra refusé. Autorisez dans le navigateur.';
        else if (err.name === 'NotFoundError') this.cameraError = 'Aucune caméra détectée.';
        else this.cameraError = 'Erreur caméra : ' + (err.message || err.name);
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
    if (this.scanSuccess) this.loadData();
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

    const snapshotDataUrl = canvas.toDataURL('image/jpeg', 0.85);

    canvas.toBlob((blob) => {
      this.zone.run(() => {
        if (!blob) {
          this.scanLoading = false; this.scanStatus = '';
          this.scanError = 'Impossible de capturer l\'image.';
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
            this.scanLoading = false; this.scanStatus = '';
            if (res.status === 'success') {
              this.scanSuccess = `Visage de ${res.employeeName || this.activeEmployee!.name} enregistré !`;
              this.stopStream();
              const emp = this.employees.find(e => e.id === this.activeEmployee!.id);
              if (emp) {
                emp.faceRegistered = true;
                emp.facePhotoData  = snapshotDataUrl;
              }
              setTimeout(() => this.closeModal(), 1500);
            } else {
              this.scanError = res.message || 'Aucun visage détecté. Regardez directement la caméra.';
            }
          },
          error: (err) => {
            this.scanLoading = false; this.scanStatus = '';
            if (err.name === 'TimeoutError' || err.constructor?.name === 'TimeoutError') {
              this.scanError = '⏱ Délai dépassé (25s). Vérifiez que le serveur IA (port 8000) est démarré.';
            } else {
              this.scanError = err.error?.message || err.error?.error || 'Erreur serveur.';
            }
          }
        });
      });
    }, 'image/jpeg', 0.85);
  }

  openCreateForm() {
    this.newEmployee = { name: '', email: '', phone: '', job: 'WORKER' };
    this.createError   = '';
    this.createSuccess = '';
    this.showCreateForm = true;
  }

  cancelCreateForm() {
    this.showCreateForm = false;
    this.createError   = '';
    this.createSuccess = '';
  }

  submitCreateEmployee() {
    if (!this.newEmployee.name.trim()) {
      this.createError = 'Le nom est obligatoire.';
      return;
    }
    this.createLoading = true;
    this.createError   = '';
    this.createSuccess = '';

    const payload: any = {
      name:   this.newEmployee.name.trim(),
      email:  this.newEmployee.email.trim() || null,
      phone:  this.newEmployee.phone.trim() || null,
      job:    this.newEmployee.job,
      status: 'PENDING',
      faceRegistered: false
    };

    this.employeeService.create(payload).subscribe({
      next: (saved: any) => {
        this.createLoading = false;
        this.createSuccess = `${saved.name} a été ajouté avec succès !`;
        this.employees.push(saved);
        setTimeout(() => {
          this.showCreateForm = false;
          this.createSuccess = '';
        }, 2000);
      },
      error: (err: any) => {
        this.createLoading = false;
        this.createError = err?.error?.message || err?.error || 'Erreur lors de la création.';
      }
    });
  }

  logout()      { localStorage.clear(); this.router.navigate(['/login']); }
  switchView(v: 'dashboard' | 'employees' | 'settings') { this.currentView = v; }
  scrollTo(id: string) {
    this.currentView = 'dashboard';
    setTimeout(() => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }), 100);
  }

  getUnregisteredEmployees() { return this.employees.filter(e => !e.faceRegistered); }
  getRegisteredEmployees()   { return this.employees.filter(e =>  e.faceRegistered); }
}
