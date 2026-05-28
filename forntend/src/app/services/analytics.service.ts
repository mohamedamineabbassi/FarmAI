import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, forkJoin, interval, of, combineLatest } from 'rxjs';
import { map, switchMap, startWith, catchError } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {

  private baseUrl = 'http://localhost:8081/api';

  constructor(private http: HttpClient) { }

  getDashboardData(): Observable<any> {
    const employees$ = this.http.get<any[]>(`${this.baseUrl}/employees`).pipe(
      catchError(err => { console.warn('[Analytics] /employees error:', err); return of([]); })
    );
    const cameras$ = this.http.get<any[]>(`${this.baseUrl}/cameras`).pipe(
      catchError(err => { console.warn('[Analytics] /cameras error:', err); return of([]); })
    );
    const alerts$ = this.http.get<any[]>(`${this.baseUrl}/alerts`).pipe(
      catchError(err => { console.warn('[Analytics] /alerts error:', err); return of([]); })
    );
    const attendance$ = this.http.get<any[]>(`${this.baseUrl}/attendance`).pipe(
      catchError(err => { console.warn('[Analytics] /attendance error:', err); return of([]); })
    );

    return forkJoin({
      employees: employees$,
      cameras: cameras$,
      alerts: alerts$,
      attendance: attendance$
    });
  }

  getDashboardDataWithPolling(pollIntervalMs: number = 10000): Observable<any> {
    return interval(pollIntervalMs).pipe(
      startWith(0),
      switchMap(() => this.getDashboardData())
    );
  }

}
