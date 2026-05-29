import { Component, OnInit } from '@angular/core';
import { AttendanceService, AttendanceRecord } from '../services/attendance.service';

@Component({
  selector: 'app-attendance',
  templateUrl: './attendance.component.html',
  styleUrls: ['./attendance.component.scss']
})
export class AttendanceComponent implements OnInit {

  records: AttendanceRecord[] = [];
  loading = true;
  searchTerm = '';
  searchTimeout: any;

  readonly BASE_URL = 'http://localhost:8081/';

  constructor(private attendanceService: AttendanceService) {}

  ngOnInit(): void {
    this.loadAttendances();
  }

  loadAttendances(name?: string): void {
    this.loading = true;
    this.attendanceService.getAll(name).subscribe({
      next: (data) => {
        this.records = data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  onSearchChange(): void {
    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(() => {
      this.loadAttendances(this.searchTerm);
    }, 400);
  }

  clearSearch(): void {
    this.searchTerm = '';
    this.loadAttendances();
  }

  getImageUrl(imagePath: string): string {
    if (!imagePath) return '';
    if (imagePath.startsWith('http')) return imagePath;
    // Remove leading slash if present to avoid double-slash
    const clean = imagePath.startsWith('/') ? imagePath.slice(1) : imagePath;
    return this.BASE_URL + clean;
  }

  getStatusLabel(status: string, unknown: boolean): string {
    if (unknown) return 'INCONNU';
    if (!status) return '—';
    return status.toUpperCase() === 'ENTRY' ? 'ENTRÉE'
         : status.toUpperCase() === 'EXIT'  ? 'SORTIE'
         : status.toUpperCase();
  }

  getStatusClass(status: string, unknown: boolean): string {
    if (unknown) return 'status-unknown';
    if (!status) return '';
    const s = status.toUpperCase();
    if (s === 'ENTRY') return 'status-entry';
    if (s === 'EXIT')  return 'status-exit';
    return 'status-other';
  }

  getTodayEntries(): number {
    const today = new Date().toDateString();
    return this.records.filter(r =>
      !r.unknown && r.status?.toUpperCase() === 'ENTRY' &&
      new Date(r.timestamp).toDateString() === today
    ).length;
  }

  getTodayExits(): number {
    const today = new Date().toDateString();
    return this.records.filter(r =>
      !r.unknown && r.status?.toUpperCase() === 'EXIT' &&
      new Date(r.timestamp).toDateString() === today
    ).length;
  }

  formatDuration(seconds?: number | null): string {
    if (seconds == null) return '';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}h ${m}min`;
    if (m > 0) return `${m}min ${s}s`;
    return `${s}s`;
  }

  getTodayUnknown(): number {
    const today = new Date().toDateString();
    return this.records.filter(r =>
      r.unknown && new Date(r.timestamp).toDateString() === today
    ).length;
  }
}
