import { Component, OnInit } from '@angular/core';
import { AlertService, Alert } from '../services/alert.service';

@Component({
  selector: 'app-alerts',
  templateUrl: './alerts.component.html',
  styleUrls: ['./alerts.component.scss']
})
export class AlertsComponent implements OnInit {

  alerts: Alert[] = [];
  activeCount: number = 0;
  serverUrl = 'http://localhost:8081';
  private previousAlertIds = new Set<number>();

  constructor(private service: AlertService) {}

  ngOnInit(): void {
    this.load();

    // 🔥 refresh automatique
    setInterval(() => this.load(), 3000);
  }

  load(): void {
    // 1. Charger les alertes limitées
    this.service.getUnresolved().subscribe({
      next: (res) => {
        this.alerts = res;
        
        let hasNewAlert = false;
        const currentIds = new Set<number>();
        
        this.alerts.forEach(alert => {
            if (alert.id) {
                currentIds.add(alert.id);
                if (!this.previousAlertIds.has(alert.id)) {
                    if (alert.severity === 'CRITICAL' || alert.severity === 'HIGH') {
                        hasNewAlert = true;
                    }
                }
            }
        });
        
        if (hasNewAlert && this.previousAlertIds.size > 0) {
            this.playSound();
        }
        
        this.previousAlertIds = currentIds;
      },
      error: (err) => {
        console.error(err);
      }
    });

    // 2. Charger le vrai compte total d'alertes actives
    this.service.getActiveCount().subscribe({
      next: (res) => {
         this.activeCount = res.activeCount;
      },
      error: (err) => console.error(err)
    });
  }
  
  playSound(): void {
    try {
        const audio = new Audio('assets/notification.mp3');
        audio.play().catch(e => console.log('Audio play blocked by browser', e));
    } catch (e) {}
  }

  resolve(id?: number): void {
    if (!id) return;
    
    // Décrémentation visuelle immédiate (optimisation UX)
    this.alerts = this.alerts.filter(a => a.id !== id);
    if (this.activeCount > 0) this.activeCount--;
    
    this.service.resolveAlert(id).subscribe({
      next: () => {
         // Le polling fera le reste, pas besoin de reload manuel synchrone
      },
      error: (err) => {
         console.error(err);
         this.load(); // Rollback visuel en cas d'erreur
      }
    });
  }
}
