import { Component, OnInit, OnDestroy, AfterViewInit, ViewChildren, QueryList, ElementRef } from '@angular/core';
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

  @ViewChildren('videoPlayer') videoPlayers!: QueryList<ElementRef<HTMLVideoElement>>;

  cameras: Camera[] = [];
  departments: any[] = [];
  sharedStream: MediaStream | null = null;
  private isCapturingStream = false;
  cameraInitialized = false;
  imgTimestamp = Date.now();
  aiStatus: {[key: number]: boolean} = {}; // 🔥 Suivi par caméra

  editMode = false;
  editId?: number;

  refreshSub?: Subscription; // 🔥 REFRESH

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

  // =========================
  // INIT
  // =========================
  ngOnInit(): void {
    this.loadCameras();
    this.loadDepartments();
    this.updateAllAIStatus();

    // 🔁 REFRESH AUTOMATIQUE (Plus rapide pour le flux image)
    this.refreshSub = interval(3000).subscribe(() => {
      this.imgTimestamp = Date.now();
      this.loadCameras();
      this.updateAllAIStatus();
    });
  }

  ngAfterViewInit() {
    // Detect when video elements appear/change in the DOM
    this.videoPlayers.changes.subscribe(() => {
      this.assignSharedStream();
    });
  }

  // =========================
  // DESTROY (important)
  // =========================
  ngOnDestroy(): void {
    this.refreshSub?.unsubscribe();
    this.stopSharedStream();
  }


  // =========================
  // LOAD CAMERAS
  // =========================
  loadCameras() {
    this.cameraService.getAll().subscribe(res => {
      this.cameras = res;
      
      // ✅ L'Angular ne tente plus de capturer la webcam localement
      // Tout est délégué au SOC AI Engine qui s'en occupe en arrière-plan.
    });
  }

  // =========================
  // LOAD DEPARTMENTS
  // =========================
  loadDepartments() {
    this.departmentService.getDepartments()
      .subscribe(res => this.departments = res);
  }

  // =========================
  // EDIT
  // =========================
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

  // =========================
  // SAVE / UPDATE
  // =========================
  save() {

    const payload: Camera = {
      name: this.cameraForm.name,
      type: this.cameraForm.type,
      source: this.cameraForm.source,
      status: 'OFF',
      location: this.cameraForm.location,
      department: {
        id: Number(this.cameraForm.departmentId)
      }
    };

    if (this.editMode && this.editId) {

      this.cameraService.update(this.editId, payload)
        .subscribe(() => {
          alert("Camera modifiée ✅");
          this.resetForm();
          this.loadCameras();
        });

    } else {

      this.cameraService.create(payload)
        .subscribe(() => {
          alert("Camera ajoutée ✅");
          this.resetForm();
          this.loadCameras();
        });
    }
  }

  // =========================
  // DELETE
  // =========================
  delete(id?: number) {
    if (!id) return;

    if (confirm("Supprimer ?")) {
      this.cameraService.delete(id)
        .subscribe(() => this.loadCameras());
    }
  }

  // =========================
  // 📹 AUTO ADD WEBCAM
  // =========================
  addingWebcam = false;

  addWebcamAuto() {
    this.addingWebcam = true;

    // Check if webcam camera already exists (source = '0' or 'local')
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

    // Create new webcam camera entry
    const payload: Camera = {
      name: 'WEBCAM-LOCAL',
      type: 'FACE_RECOGNITION',
      source: '0',
      status: 'ACTIVE', // On l'active par défaut
      location: 'Poste Principal',
      department: this.departments.length > 0 ? { id: this.departments[0].id } : undefined as any
    };

    this.cameraService.create(payload).subscribe({
      next: (created) => {
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

  // =========================
  // RESET
  // =========================
  resetForm() {
    this.cameraForm = {
      name: '',
      type: '',
      location: '',
      source: '',
      departmentId: null
    };
    this.editMode = false;
    this.editId = undefined;
  }

  // =========================
  // AI CONTROL (PER CAMERA)
  // =========================
  updateAllAIStatus() {
    this.cameras.forEach(cam => {
      if (cam.id) this.checkAIStatus(cam.id);
    });
  }

  checkAIStatus(cameraId: number) {
    this.http.get<{status: string, active_cameras: number[]}>(`http://localhost:8000/api/engine/status`)
      .subscribe({
        next: (res) => {
          this.aiStatus[cameraId] = res.active_cameras.includes(cameraId);
        },
        error: () => {
          this.aiStatus[cameraId] = false;
        }
      });
  }

  toggleAI(cam: Camera) {
    if (!cam.id) return;
    
    // Si c'était actif, on le désactive. Sinon on l'active.
    const newStatus = cam.status === 'ACTIVE' ? 'OFF' : 'ACTIVE';
    
    const payload: Camera = {
      ...cam,
      status: newStatus
    };

    this.cameraService.update(cam.id, payload).subscribe(() => {
      cam.status = newStatus;
      this.loadCameras();
      // On force une vérification après un petit délai pour le temps de démarrage python
      setTimeout(() => this.updateAllAIStatus(), 3000);
    });
  }

  // =========================
  // CAMERA STREAM LOGIC
  // =========================
  isUrl(source: string): boolean {
    return source?.startsWith('http') || source?.startsWith('ws');
  }

  isLocal(source: string): boolean {
    return source === '0' || source === '1' || source?.toLowerCase() === 'local';
  }

  getSafeUrl(source: string): SafeResourceUrl {
    return this.sanitizer.bypassSecurityTrustResourceUrl(source);
  }

  initSharedWebcam() {
    if (this.sharedStream || this.isCapturingStream) return;

    this.isCapturingStream = true;
    console.log("📸 CAPTURING SHARED WEBCAM STREAM...");
    
    navigator.mediaDevices.getUserMedia({ 
      video: { width: 1280, height: 720 }, 
      audio: false 
    })
    .then(stream => {
      this.sharedStream = stream;
      this.isCapturingStream = false;
      this.assignSharedStream();
    })
    .catch(err => {
      this.isCapturingStream = false;
      console.error("❌ Erreur d'accès à la webcam locale", err);
    });
  }

  assignSharedStream() {
    if (!this.sharedStream || !this.videoPlayers) return;

    const players = this.videoPlayers.toArray();
    
    // 🔥 Si aucun élément <video> n'est dans le DOM, on peut libérer le flux
    if (players.length === 0) {
      this.stopSharedStream();
      return;
    }

    players.forEach(player => {
      const video = player.nativeElement;
      if (!video.srcObject) {
        console.log("🔗 ATTACHING STREAM TO VIDEO ELEMENT:", video.id);
        video.srcObject = this.sharedStream;
        video.play().catch(e => console.warn("Auto-play blocked or failed:", e));
      }
    });
  }

  stopSharedStream() {
    if (this.sharedStream) {
      this.sharedStream.getTracks().forEach(track => track.stop());
      this.sharedStream = null;
    }
  }
}
