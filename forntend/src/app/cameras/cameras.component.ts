import { Component, OnInit, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { CameraService, Camera } from '../services/camera.service';
import { DepartmentService } from '../services/department.service';
import { interval, Subscription } from 'rxjs';

@Component({
  selector: 'app-cameras',
  templateUrl: './cameras.component.html',
  styleUrls: ['./cameras.component.scss']
})
export class CamerasComponent implements OnInit, OnDestroy {

  cameras: Camera[] = [];
  departments: any[] = [];
  imgTimestamp = Date.now();
  aiStatus: { [key: number]: boolean } = {};

  editMode = false;
  editId?: number;
  addingWebcam = false;

  refreshSub?: Subscription;

  cameraForm: any = {
    name: '',
    type: '',
    location: '',
    source: '',
    departmentId: null
  };

  constructor(
    private cameraService: CameraService,
    private departmentService: DepartmentService,
    private http: HttpClient,
    private sanitizer: DomSanitizer
  ) {}

  ngOnInit(): void {
    this.loadCameras();
    this.loadDepartments();
    this.updateAllAIStatus();

    this.refreshSub = interval(3000).subscribe(() => {
      this.imgTimestamp = Date.now();
      this.loadCameras();
      this.updateAllAIStatus();
    });
  }

  ngOnDestroy(): void {
    this.refreshSub?.unsubscribe();
  }

  loadCameras() {
    this.cameraService.getAll().subscribe(res => {
      this.cameras = res;
    });
  }

  loadDepartments() {
    this.departmentService.getDepartments()
      .subscribe(res => this.departments = res);
  }

  edit(c: Camera) {
    this.cameraForm = {
      name: c.name,
      type: c.type,
      location: c.location,
      source: c.source,
      departmentId: c.department?.id
    };
    this.editMode = true;
    this.editId = c.id;
  }

  save() {
    const payload: Camera = {
      name: this.cameraForm.name,
      type: this.cameraForm.type,
      source: this.cameraForm.source,
      status: 'OFF',
      location: this.cameraForm.location,
      department: { id: Number(this.cameraForm.departmentId) }
    };

    if (this.editMode && this.editId) {
      this.cameraService.update(this.editId, payload).subscribe(() => {
        alert('Camera modifiée ✅');
        this.resetForm();
        this.loadCameras();
      });
    } else {
      this.cameraService.create(payload).subscribe(() => {
        alert('Camera ajoutée ✅');
        this.resetForm();
        this.loadCameras();
      });
    }
  }

  delete(id?: number) {
    if (!id) return;
    if (confirm('Supprimer ?')) {
      this.cameraService.delete(id).subscribe(() => this.loadCameras());
    }
  }

  addWebcamAuto() {
    this.addingWebcam = true;

    const existing = this.cameras.find(c => c.source === '0' || c.source === 'local');

    if (existing) {
      if (existing.id && existing.status !== 'ACTIVE') {
        existing.status = 'ACTIVE';
        this.cameraService.update(existing.id, existing).subscribe({
          next: () => {
            this.addingWebcam = false;
            alert('✅ Webcam activée ! L\'IA SOC démarre le flux vidéo...');
            this.loadCameras();
            setTimeout(() => this.updateAllAIStatus(), 3000);
          },
          error: (err) => {
            this.addingWebcam = false;
            alert('❌ Erreur activation: ' + err.message);
          }
        });
      } else {
        this.addingWebcam = false;
        alert('⚠️ La webcam est déjà en cours d\'exécution !');
      }
      return;
    }

    const payload: Camera = {
      name: 'WEBCAM-LOCAL',
      type: 'FACE_RECOGNITION',
      source: '0',
      status: 'ACTIVE',
      location: 'Poste Principal',
      department: this.departments.length > 0 ? { id: this.departments[0].id } : undefined as any
    };

    this.cameraService.create(payload).subscribe({
      next: () => {
        this.addingWebcam = false;
        alert('✅ Webcam ajoutée et activée ! Le moteur SOC s\'en occupe...');
        this.loadCameras();
        setTimeout(() => this.updateAllAIStatus(), 3000);
      },
      error: (err) => {
        this.addingWebcam = false;
        alert('❌ Erreur: ' + (err.error?.message || 'Impossible d\'ajouter la webcam'));
      }
    });
  }

  resetForm() {
    this.cameraForm = { name: '', type: '', location: '', source: '', departmentId: null };
    this.editMode = false;
    this.editId = undefined;
  }

  updateAllAIStatus() {
    this.cameras.forEach(cam => {
      if (cam.id) this.checkAIStatus(cam.id);
    });
  }

  checkAIStatus(cameraId: number) {
    this.http.get<{ status: string; active_cameras: number[] }>(`http://localhost:8000/api/engine/status`)
      .subscribe({
        next: (res) => { this.aiStatus[cameraId] = res.active_cameras.includes(cameraId); },
        error: () => { this.aiStatus[cameraId] = false; }
      });
  }

  toggleAI(cam: Camera) {
    if (!cam.id) return;
    const newStatus = cam.status === 'ACTIVE' ? 'OFF' : 'ACTIVE';
    const payload: Camera = { ...cam, status: newStatus };

    this.cameraService.update(cam.id, payload).subscribe(() => {
      cam.status = newStatus;
      this.loadCameras();
      setTimeout(() => this.updateAllAIStatus(), 3000);
    });
  }

  isUrl(source: string): boolean {
    return source?.startsWith('http') || source?.startsWith('ws');
  }

  isLocal(source: string): boolean {
    return source === '0' || source === '1' || source?.toLowerCase() === 'local';
  }

  getSafeUrl(source: string): SafeResourceUrl {
    return this.sanitizer.bypassSecurityTrustResourceUrl(source);
  }
}
