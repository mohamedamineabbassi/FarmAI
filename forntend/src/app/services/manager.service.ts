import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Manager {
  id?: number;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  enabled?: boolean;
  faceRegistered?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ManagerService {

  API = 'http://localhost:8081/api/users';

  constructor(private http: HttpClient) {}

  getManagers(): Observable<Manager[]> {
    return this.http.get<Manager[]>(`${this.API}/managers`);
  }

  create(manager: Manager) {
    return this.http.post(`${this.API}/managers`, manager);
  }

  update(id: number, manager: Manager) {
    return this.http.put(`${this.API}/managers/${id}`, manager);
  }

  delete(id: number) {
    return this.http.delete(`${this.API}/managers/${id}`);
  }
}
