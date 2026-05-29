import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AttendanceRecord {
  id: number;
  employeeName: string;
  employeeId: number | null;
  status: string;
  unknown: boolean;
  imagePath: string;
  timestamp: string;
  durationSeconds?: number | null;
}

@Injectable({
  providedIn: 'root'
})
export class AttendanceService {

  private API = 'http://localhost:8081/api/attendance';

  constructor(private http: HttpClient) {}

  getAll(nameFilter?: string): Observable<AttendanceRecord[]> {
    let params = new HttpParams();
    if (nameFilter && nameFilter.trim()) {
      params = params.set('name', nameFilter.trim());
    }
    return this.http.get<AttendanceRecord[]>(this.API, { params });
  }
}
