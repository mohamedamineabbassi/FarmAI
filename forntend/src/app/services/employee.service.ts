import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Employee {
  id?: number;
  name: string;
  email?: string;
  phone?: string;
  job: string;
  status: string;
  faceRegistered: boolean;
  facePhotoData?: string;
}

@Injectable({
  providedIn: 'root'
})
export class EmployeeService {

  API = 'http://localhost:8081/api/employees';

  constructor(private http: HttpClient) {}

  getAll(): Observable<Employee[]> {
    return this.http.get<Employee[]>(this.API);
  }

  getMyProfile(email: string): Observable<Employee> {
    return this.http.get<Employee>(`${this.API}/me?email=${email}`);
  }

  getById(id: number): Observable<Employee> {
    return this.http.get<Employee>(`${this.API}/${id}`);
  }

  update(id: number, emp: Partial<Employee>): Observable<Employee> {
    return this.http.put<Employee>(`${this.API}/${id}`, emp);
  }

  getEmployees(): Observable<Employee[]> {
    return this.http.get<Employee[]>(`${this.API}/only-employees`);
  }

  getWithoutFace(): Observable<Employee[]> {
    return this.http.get<Employee[]>(`${this.API}/no-face`);
  }

  create(emp: Employee) {
    return this.http.post(`${this.API}/employee`, emp);
  }

  delete(id: number) {
    return this.http.delete(`${this.API}/${id}`, { responseType: 'text' });
  }

  registerFace(id: number) {
    return this.http.post(`${this.API}/register-face/${id}`, {});
  }

  deleteFace(id: number) {
    return this.http.delete(`${this.API}/delete-face/${id}`);
  }

  validateFace(id: number) {
    return this.http.put(`${this.API}/validate-face/${id}`, {});
  }

  approve(id: number) {
    return this.http.post(`${this.API}/approve/${id}`, {});
  }
}
