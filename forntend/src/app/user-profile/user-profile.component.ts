import { Component, OnInit, OnDestroy, ViewChild, ElementRef, NgZone, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { timeout } from 'rxjs/operators';
import { EmployeeService, Employee } from '../services/employee.service';

@Component({
  selector: 'app-user-profile',
  templateUrl: './user-profile.component.html',
  styleUrls: ['./user-profile.component.css']
})
export class UserProfileComponent implements OnInit, OnDestroy {

  currentEmployee: Employee | null = null;
  loading = false;
  message = '';
  isError = false;

  // true when an admin/manager is viewing a specific employee (id query param)
  viewingOther = false;

  // Edit Profile fields (bound to the form)
  editName = '';
  editEmail = '';
  editPhone = '';

  // ── Camera modal ──────────────────────────────────────────────
  showCameraModal = false;
  cameraReady     = false;
  scanLoading     = false;
  scanStatus      = '';
  scanSuccess     = '';
  scanError       = '';

  @ViewChild('captureVideo', { static: false }) captureVideo!: ElementRef<HTMLVideoElement>;
  private mediaStream: MediaStream | null = null;

  constructor(
    private employeeService: EmployeeService,
    private route: ActivatedRoute,
    private http: HttpClient,
    private zone: NgZone,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      const id = params['id'];
      if (id) {
        this.viewingOther = true;
        this.loadById(Number(id));
      } else {
        this.viewingOther = false;
        this.loadCurrentEmployee();
      }
    });
  }

  ngOnDestroy() {
    this.stopStream();
  }

  loadById(id: number) {
    this.loading = true;
    this.employeeService.getById(id).subscribe(employee => {
      this.loading = false;
      this.applyEmployee(employee);
    }, err => {
      this.loading = false;
      console.error('ERROR LOADING PROFILE:', err);
      this.message = "❌ Impossible de charger le profil de cet employé.";
      this.isError = true;
    });
  }

  loadCurrentEmployee() {
    const email = localStorage.getItem('email');
    if (!email) {
      this.message = "❌ Aucune session active.";
      this.isError = true;
      return;
    }

    this.loading = true;
    this.employeeService.getMyProfile(email).subscribe(employee => {
      this.loading = false;
      this.applyEmployee(employee);
    }, err => {
      this.loading = false;
      console.error('ERROR LOADING PROFILE:', err);
      this.message = "❌ Impossible de charger votre profil.";
      this.isError = true;
    });
  }

  private applyEmployee(employee: Employee) {
    this.currentEmployee = employee;
    this.editName  = employee.name || '';
    this.editEmail = employee.email || '';
    this.editPhone = employee.phone || '';
    this.message = '';
    this.isError = false;
  }

  // ── Update profile info ────────────────────────────────────────
  updateProfile() {
    if (!this.currentEmployee?.id) {
      this.message = "❌ Profil non lié : aucun enregistrement employé trouvé.";
      this.isError = true;
      return;
    }
    if (!this.editName || !this.editName.trim()) {
      this.message = "❌ Le nom est obligatoire.";
      this.isError = true;
      return;
    }

    this.loading = true;
    this.message = 'Mise à jour en cours...';
    this.isError = false;

    this.employeeService.update(this.currentEmployee.id, {
      name:  this.editName.trim(),
      email: this.editEmail,
      phone: this.editPhone
    }).subscribe(updated => {
      this.loading = false;
      this.applyEmployee(updated);
      this.message = '✅ Profil mis à jour avec succès !';
      this.isError = false;
      setTimeout(() => this.message = '', 3000);
    }, err => {
      this.loading = false;
      console.error('UPDATE ERROR:', err);
      this.message = err.error?.message || '❌ Erreur lors de la mise à jour.';
      this.isError = true;
    });
  }

  // ── Face biometrics (browser camera) ───────────────────────────
  openCamera() {
    if (!this.currentEmployee?.id) {
      this.message = "❌ Profil non lié : impossible d'enregistrer le visage.";
      this.isError = true;
      return;
    }
    this.cameraReady  = false;
    this.scanLoading  = false;
    this.scanStatus   = '';
    this.scanSuccess  = '';
    this.scanError    = '';
    this.showCameraModal = true;
    setTimeout(() => this.startCamera(), 250);
  }

  startCamera() {
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
        if (err.name === 'NotAllowedError')        this.scanStatus = 'Accès caméra refusé. Autorisez dans le navigateur.';
        else if (err.name === 'NotFoundError')     this.scanStatus = 'Aucune caméra détectée.';
        else if (err.name === 'NotReadableError')  this.scanStatus = 'Caméra déjà utilisée par une autre application.';
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
    if (this.scanSuccess && this.currentEmployee?.id) {
      // refresh to pick up faceRegistered + photo
      if (this.viewingOther) this.loadById(this.currentEmployee.id);
      else this.loadCurrentEmployee();
    }
  }

  onOverlayClick(event: MouseEvent) {
    if (event.target === event.currentTarget) this.closeModal();
  }

  doScan() {
    if (!this.currentEmployee?.id) return;
    const video = this.captureVideo?.nativeElement;
    if (!video || !this.mediaStream || video.videoWidth === 0) {
      this.scanError = 'Caméra non prête. Attendez et réessayez.';
      return;
    }

    this.scanLoading = true;
    this.scanError   = '';
    this.scanSuccess = '';
    this.scanStatus  = "Capture de l'image...";

    const canvas = document.createElement('canvas');
    canvas.width  = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')!.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      this.zone.run(() => {
        if (!blob) {
          this.scanLoading = false;
          this.scanStatus  = '';
          this.scanError   = "Impossible de capturer l'image.";
          return;
        }

        this.scanStatus = 'Analyse IA en cours...';
        const form = new FormData();
        form.append('image', blob, 'face.jpg');

        this.http.post<any>(
          `http://localhost:8081/api/employees/register-face-image/${this.currentEmployee!.id}`,
          form
        )
        .pipe(timeout(25000))
        .subscribe({
          next: (res) => {
            this.scanLoading = false;
            this.scanStatus  = '';
            if (res.status === 'success') {
              this.scanSuccess = `✅ Visage de ${res.employeeName || this.currentEmployee!.name} enregistré !`;
              this.stopStream();
              if (this.currentEmployee) this.currentEmployee.faceRegistered = true;
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

  deleteFace() {
    if (!this.currentEmployee?.id) return;
    if (!confirm('Voulez-vous vraiment supprimer les données biométriques ?')) return;

    this.loading = true;
    this.employeeService.deleteFace(this.currentEmployee.id).subscribe(() => {
      this.loading = false;
      this.message = '✅ Données biométriques supprimées.';
      this.isError = false;
      if (this.currentEmployee) {
        this.currentEmployee.faceRegistered = false;
        this.currentEmployee.facePhotoData = undefined;
      }
    }, err => {
      this.loading = false;
      console.error('DELETE FACE ERROR:', err);
      this.message = '❌ Erreur lors de la suppression des données biométriques.';
      this.isError = true;
    });
  }
}
