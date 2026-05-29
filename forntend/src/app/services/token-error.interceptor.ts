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
 * Intercepteur global pour gérer les erreurs d'authentification/autorisation.
 *
 * - 401 : token absent ou expiré → déconnexion automatique
 * - 403 sur un endpoint admin : token valide mais mauvais rôle → déconnexion
 *         (évite les boucles d'erreurs infinies si le token est corrompu)
 */
@Injectable()
export class TokenErrorInterceptor implements HttpInterceptor {

  // Endpoints qui nécessitent ROLE_ADMIN — un 403 ici = mauvais token → re-login
  private readonly adminEndpoints = [
    '/api/employees/approve',
    '/api/face-notifications',
    '/api/managers',
    '/api/viewers',
    '/api/users'
  ];

  constructor(private router: Router) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Les endpoints d'authentification (login, face-login, activation...) gèrent
    // eux-mêmes leurs erreurs. Un 401 ici = identifiants invalides, PAS une session
    // expirée → on ne déclenche pas la déconnexion/redirection (sinon boucle de login).
    const isAuthEndpoint = req.url.includes('/api/auth/');

    return next.handle(req).pipe(
      catchError((err: HttpErrorResponse) => {

        if (err.status === 401 && !isAuthEndpoint) {
          // Token expiré ou manquant
          console.warn('🔒 Session expirée — reconnexion requise');
          localStorage.clear();
          this.router.navigate(['/login'], {
            queryParams: { sessionExpired: 'true' }
          });
        } else if (err.status === 403) {
          // Vérifie si c'est un endpoint admin — si oui, le token est invalide
          const isAdminEndpoint = this.adminEndpoints.some(ep => req.url.includes(ep));
          const role = localStorage.getItem('role');
          if (isAdminEndpoint && role === 'ROLE_ADMIN') {
            // L'utilisateur pense être admin mais le backend refuse → token corrompu
            console.warn('🔒 Token invalide pour endpoint admin — reconnexion requise');
            localStorage.clear();
            this.router.navigate(['/login'], {
              queryParams: { sessionExpired: 'true' }
            });
          }
        }

        return throwError(() => err);
      })
    );
  }
}
