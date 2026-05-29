import { Component, OnInit } from '@angular/core';

interface QuickLink {
  label: string;
  icon: string;
  route: string;
  gradient: string;
  desc: string;
}

@Component({
  selector: 'app-welcome',
  templateUrl: './welcome.component.html',
  styleUrls: ['./welcome.component.scss']
})
export class WelcomeComponent implements OnInit {

  userEmail = '';
  userName = '';
  today = new Date();

  quickLinks: QuickLink[] = [
    { label: 'Départements', icon: 'apartment',           route: '/dashboard/departments', gradient: 'linear-gradient(135deg,#4caf50,#388e3c)', desc: 'Unités opérationnelles' },
    { label: 'Caméras',      icon: 'videocam',            route: '/dashboard/cameras',     gradient: 'linear-gradient(135deg,#0ea5e9,#0284c7)', desc: 'Surveillance temps réel' },
    { label: 'Employés',     icon: 'people',              route: '/dashboard/employees',   gradient: 'linear-gradient(135deg,#8b5cf6,#6d28d9)', desc: 'Gestion du personnel' },
    { label: 'Présences',    icon: 'sensor_door',         route: '/dashboard/attendance',  gradient: 'linear-gradient(135deg,#f59e0b,#d97706)', desc: 'Entrées / Sorties' },
    { label: 'Analyses AI',  icon: 'analytics',           route: '/dashboard/analytics',   gradient: 'linear-gradient(135deg,#06b6d4,#0891b2)', desc: 'Intelligence artificielle' },
    { label: 'Alertes',      icon: 'notifications_active', route: '/dashboard/alerts',      gradient: 'linear-gradient(135deg,#ef4444,#dc2626)', desc: "Centre d'alertes" },
  ];

  ngOnInit(): void {
    this.userEmail = localStorage.getItem('email') || '';
    this.userName = this.userEmail ? this.userEmail.split('@')[0] : 'Administrateur';
  }
}
