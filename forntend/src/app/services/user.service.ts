import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

export interface User {
  id?: number;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  role?: string;
}

@Injectable({
  providedIn: 'root'
})
export class UserService {

  API = 'http://localhost:8081/api/users';

  constructor(private http: HttpClient) {}

  getViewers() {
    return this.http.get<User[]>(`${this.API}/viewers`);
  }

  createViewer(user: User) {
    return this.http.post<User>(`${this.API}/viewers`, user);
  }

  update(id: number, user: User) {
    return this.http.put<User>(`${this.API}/viewers/${id}`, user);
  }

  delete(id: number) {
    return this.http.delete(`${this.API}/viewers/${id}`);
  }

  activate(token: string) {
    return this.http.post(`http://localhost:8081/api/auth/activate?token=${token}`, {});
  }

  registerFace(userId: number) {
    return this.http.post(`http://localhost:8081/api/auth/face/register`, { userId });
  }

  getProfile() {
    return this.http.get<User>(`${this.API}/get-profile`);
  }

  updateProfile(user: User) {
    return this.http.put(`${this.API}/update-profile`, user);
  }

  changePassword(data: any) {
    return this.http.put(`${this.API}/change-password`, data);
  }
}
