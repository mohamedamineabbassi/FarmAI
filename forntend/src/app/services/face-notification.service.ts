import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface FaceNotification {
  id: number;
  employeeId: number;
  employeeName: string;
  employeeEmail: string;
  employeeJob: string;
  viewerEmail: string;
  faceSnapshot: string;   // data:image/jpeg;base64,...
  registeredAt: string;
  read: boolean;
}

@Injectable({ providedIn: 'root' })
export class FaceNotificationService {

  private API = 'http://localhost:8081/api/face-notifications';

  constructor(private http: HttpClient) {}

  getAll(): Observable<FaceNotification[]> {
    return this.http.get<FaceNotification[]>(this.API);
  }

  getUnreadCount(): Observable<{ count: number }> {
    return this.http.get<{ count: number }>(`${this.API}/unread-count`);
  }

  markRead(id: number): Observable<FaceNotification> {
    return this.http.put<FaceNotification>(`${this.API}/${id}/read`, {});
  }

  markAllRead(): Observable<any> {
    return this.http.put(`${this.API}/read-all`, {});
  }

  delete(id: number): Observable<any> {
    return this.http.delete(`${this.API}/${id}`);
  }
}
