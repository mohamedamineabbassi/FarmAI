import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { LanguageService } from '../../services/language.service';
import { FaceNotificationService, FaceNotification } from '../../services/face-notification.service';

declare const $: any;

export interface RouteInfo { path: string; title: string; icon: string; class: string; }
export const ROUTES: RouteInfo[] = [];

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent implements OnInit, OnDestroy {

  menuItems: any[] = [];

  notifications: FaceNotification[] = [];
  unreadCount = 0;
  showNotifPanel = false;
  selectedNotif: FaceNotification | null = null;

  private pollInterval: any;

  constructor(
    public langService: LanguageService,
    private router: Router,
    private notifService: FaceNotificationService
  ) {}

  ngOnInit() {
    this.loadUnreadCount();
    // Polling toutes les 30 secondes
    this.pollInterval = setInterval(() => this.loadUnreadCount(), 30_000);
  }

  ngOnDestroy() {
    if (this.pollInterval) clearInterval(this.pollInterval);
  }

  loadUnreadCount() {
    this.notifService.getUnreadCount().subscribe({
      next: (r) => this.unreadCount = r.count,
      error: () => {}
    });
  }

  openNotifPanel() {
    this.showNotifPanel = true;
    this.selectedNotif = null;
    this.notifService.getAll().subscribe({
      next: (list) => this.notifications = list,
      error: () => {}
    });
  }

  closeNotifPanel() {
    this.showNotifPanel = false;
    this.selectedNotif = null;
  }

  openDetail(n: FaceNotification) {
    this.selectedNotif = n;
    if (!n.read) {
      this.notifService.markRead(n.id).subscribe(() => {
        n.read = true;
        this.unreadCount = Math.max(0, this.unreadCount - 1);
      });
    }
  }

  backToList() {
    this.selectedNotif = null;
  }

  readAll() {
    this.notifService.markAllRead().subscribe(() => {
      this.notifications.forEach(n => n.read = true);
      this.unreadCount = 0;
    });
  }

  deleteNotif(n: FaceNotification, event: Event) {
    event.stopPropagation();
    this.notifService.delete(n.id).subscribe(() => {
      this.notifications = this.notifications.filter(x => x.id !== n.id);
      if (!n.read) this.unreadCount = Math.max(0, this.unreadCount - 1);
      if (this.selectedNotif?.id === n.id) this.selectedNotif = null;
    });
  }

  logout() {
    localStorage.clear();
    this.router.navigate(['/login']);
  }

  isMobileMenu() {
    return $(window).width() <= 991;
  }

  jobLabel(job: string): string {
    const map: any = { DOCTOR: 'Médecin', ELECTRICIAN: 'Électricien', WORKER: 'Ouvrier', OTHER: 'Autre' };
    return map[job] || job;
  }

  jobColor(job: string): string {
    const map: any = { DOCTOR: '#2196f3', ELECTRICIAN: '#ff9800', WORKER: '#4caf50', OTHER: '#9e9e9e' };
    return map[job] || '#9e9e9e';
  }
}
