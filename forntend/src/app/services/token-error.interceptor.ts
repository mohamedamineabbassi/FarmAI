import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Router } from '@angular/router';

/**
 * Interceptor global : gère les erreurs 401 (token expiré / manquant)
 * et 403 (permissions insuffisantes) au niveau de l'application.
 *
 * - 401 : session expirée → vider le localStorage et rediriger vers /login
 * - 403 : on laisse passer pour que chaque composant affiche son propre message d'erreur
 */
@Injectable()
export class TokenErrorInterceptor implements HttpInterceptor {

  constructor(private router: Router) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return next.handle(req).pipe(
      catchError((err: HttpErrorResponse) => {

        if (err.status === 401) {
          // Token expiré ou manquant : déconnexion automatique
          console.warn('🔒 Session expirée — reconnexion requise');
          localStorage.clear();
          this.router.navigate(['/login'], {
            queryParams: { sessionExpired: 'true' }
          });
        }

        // Pour le 403, on propage l'erreur pour que chaque composant la gère
        return throwError(() => err);
      })
    );
  }
}
