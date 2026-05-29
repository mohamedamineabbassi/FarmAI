import {
  Component, OnDestroy, ViewChild, ElementRef, ChangeDetectorRef, NgZone
} from '@angular/core';
import { HttpClient } from '@angular/common/http';

interface CheckinEvent {
  employeeName: string;
  attendanceStatus: 'ENTRY' | 'EXIT' | string;
  durationSeconds: number | null;
  time: Date;
}

@Component({
  selector: 'app-faceid-attendance',
  templateUrl: './faceid-attendance.component.html',
  styleUrls: ['./faceid-attendance.component.scss']
})
export class FaceIdAttendanceComponent implements OnDestroy {

  @ViewChild('video', { static: false }) videoRef!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvas', { static: false }) canvasRef!: ElementRef<HTMLCanvasElement>;

  // Endpoints
  private readonly AI_RECOGNIZE = 'http://localhost:8000/api/face/recognize';
  private readonly BACKEND_CHECKIN = 'http://localhost:8081/api/attendance/checkin';

  // Cadence du scan + anti-doublon par personne
  private readonly SCAN_INTERVAL_MS = 2500;
  private readonly PERSON_COOLDOWN_MS = 60000; // 60s : on ne re-pointe pas la même personne

  running = false;
  starting = false;
  processing = false;
  statusMsg = 'Caméra arrêtée. Cliquez sur « Démarrer le pointage ».';
  statusType: 'idle' | 'scan' | 'ok' | 'warn' | 'err' = 'idle';

  lastEvent: CheckinEvent | null = null;
  events: CheckinEvent[] = [];

  private stream: MediaStream | null = null;
  private timer: any = null;
  private cooldown = new Map<string, number>(); // email -> dernier pointage (ms)

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) {}

  ngOnDestroy(): void {
    this.stop();
  }

  async start(): Promise<void> {
    if (this.running || this.starting) return;
    this.starting = true;
    this.setStatus('Initialisation de la caméra...', 'scan');
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false
      });
      const video = this.videoRef.nativeElement;
      video.srcObject = this.stream;
      await video.play().catch(() => { /* autoplay déjà géré par muted/playsinline */ });

      this.running = true;
      this.starting = false;
      this.setStatus('Caméra active — présentez-vous face à la caméra.', 'scan');

      this.zone.runOutsideAngular(() => {
        this.timer = setInterval(() => this.scanTick(), this.SCAN_INTERVAL_MS);
      });
    } catch (err: any) {
      this.starting = false;
      this.running = false;
      this.setStatus("Impossible d'accéder à la webcam : " + (err?.message || err), 'err');
    }
  }

  stop(): void {
    if (this.timer) { clearInterval(this.timer); this.timer = null; }
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }
    if (this.videoRef?.nativeElement) {
      this.videoRef.nativeElement.srcObject = null;
    }
    this.running = false;
    this.processing = false;
    this.setStatus('Caméra arrêtée.', 'idle');
  }

  toggle(): void {
    this.running ? this.stop() : this.start();
  }

  private scanTick(): void {
    if (!this.running || this.processing) return;
    const video = this.videoRef?.nativeElement;
    const canvas = this.canvasRef?.nativeElement;
    if (!video || !canvas || video.readyState < 2 || video.videoWidth === 0) return;

    this.processing = true;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) { this.processing = false; return; }
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (!blob) { this.processing = false; return; }
      const form = new FormData();
      form.append('image', blob, 'frame.jpg');

      // On revient dans la zone Angular pour que la détection de changement fonctionne
      this.zone.run(() => {
        this.http.post<any>(this.AI_RECOGNIZE, form).subscribe({
          next: (res) => this.handleRecognition(res),
          error: () => {
            this.setStatus('Moteur IA injoignable (port 8000). Vérifiez le SOC Engine.', 'err');
            this.processing = false;
          }
        });
      });
    }, 'image/jpeg', 0.85);
  }

  private handleRecognition(res: any): void {
    if (!res || res.status === 'error') {
      this.setStatus(res?.message || 'Erreur de reconnaissance.', 'err');
      this.processing = false;
      return;
    }
    if (res.status === 'no_face') {
      this.setStatus('Aucun visage détecté — placez-vous bien face à la caméra.', 'scan');
      this.processing = false;
      return;
    }
    if (res.status === 'no_match' || !res.email) {
      this.setStatus('Visage non reconnu.', 'warn');
      this.processing = false;
      return;
    }

    // Reconnu : anti-doublon
    const email: string = res.email;
    const now = Date.now();
    const last = this.cooldown.get(email);
    if (last && (now - last) < this.PERSON_COOLDOWN_MS) {
      const remaining = Math.ceil((this.PERSON_COOLDOWN_MS - (now - last)) / 1000);
      this.setStatus(`Déjà pointé(e) récemment — nouveau pointage possible dans ${remaining}s.`, 'warn');
      this.processing = false;
      return;
    }

    // Enregistrer le pointage (entrée/sortie automatique côté backend)
    this.http.post<any>(this.BACKEND_CHECKIN, { email }).subscribe({
      next: (r) => { this.handleCheckin(email, r); this.processing = false; },
      error: (err) => {
        let msg: string;
        if (err?.status === 0) {
          msg = 'Backend injoignable (port 8081) — vérifiez qu\'il est démarré.';
        } else if (err?.status === 404) {
          msg = 'Endpoint /checkin introuvable (404) — redémarrez le backend Spring Boot.';
        } else if (err?.status === 401 || err?.status === 403) {
          msg = `Pointage refusé (${err.status}) — problème d\'autorisation.`;
        } else {
          msg = `Erreur pointage (${err?.status || '?'}) : ${err?.error?.message || err?.message || 'inconnue'}.`;
        }
        this.setStatus(msg, 'err');
        this.processing = false;
      }
    });
  }

  private handleCheckin(email: string, r: any): void {
    if (!r) { this.setStatus('Réponse de pointage vide.', 'err'); return; }

    if (r.status === 'skipped') {
      this.setStatus(`${r.employeeName || 'Administrateur'} — non pointé (administrateur).`, 'warn');
      this.cooldown.set(email, Date.now());
      return;
    }
    if (r.status === 'unknown') {
      this.setStatus('Personne reconnue mais absente de la base.', 'warn');
      return;
    }
    if (r.status !== 'success') {
      this.setStatus(r.message || 'Pointage non enregistré.', 'err');
      return;
    }

    this.cooldown.set(email, Date.now());

    const ev: CheckinEvent = {
      employeeName: r.employeeName,
      attendanceStatus: r.attendanceStatus,
      durationSeconds: r.durationSeconds ?? null,
      time: new Date()
    };
    this.lastEvent = ev;
    this.events.unshift(ev);
    if (this.events.length > 12) this.events.pop();

    const isEntry = ev.attendanceStatus === 'ENTRY';
    if (isEntry) {
      this.setStatus(`Bienvenue ${ev.employeeName} — ENTRÉE enregistrée.`, 'ok');
    } else {
      const dur = ev.durationSeconds != null ? ` (présence : ${this.formatDuration(ev.durationSeconds)})` : '';
      this.setStatus(`Au revoir ${ev.employeeName} — SORTIE enregistrée${dur}.`, 'ok');
    }
    this.cdr.detectChanges();
  }

  private setStatus(msg: string, type: 'idle' | 'scan' | 'ok' | 'warn' | 'err'): void {
    this.statusMsg = msg;
    this.statusType = type;
    this.cdr.detectChanges();
  }

  formatDuration(seconds: number | null): string {
    if (seconds == null) return '—';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}h ${m}min`;
    if (m > 0) return `${m}min ${s}s`;
    return `${s}s`;
  }
}
