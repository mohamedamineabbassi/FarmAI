import { Component, OnInit, OnDestroy } from '@angular/core';
import * as Chartist from 'chartist';
import { AnalyticsService } from '../services/analytics.service';
import { LanguageService } from '../services/language.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-analytics',
  templateUrl: './analytics.component.html',
  styleUrls: ['./analytics.component.css']
})
export class AnalyticsComponent implements OnInit, OnDestroy {

  loading = true;
  error = false;
  lastUpdated: string = '--';
  private dataSubscription: Subscription;
  private presenceChartInstance: any = null;
  private colorChartInstance: any = null;

  get kpis() {
    return [
      { title: this.langService.t('Employés Présents', 'Employees Present Today'), value: this.kpisData[0].value, icon: 'people', color: 'purple', iconColor: '#9c27b0', trend: this.kpisData[0].trend },
      { title: this.langService.t('Heures Travaillées', 'Total Working Hours'), value: this.kpisData[1].value, icon: 'schedule', color: 'cyan', iconColor: '#00bcd4', trend: this.kpisData[1].trend },
      { title: this.langService.t('Entrées Aujourd\'hui', 'Entries Today'), value: this.kpisData[2].value, icon: 'swap_horiz', color: 'green', iconColor: '#4caf50', trend: this.kpisData[2].trend },
      { title: this.langService.t('Caméras Actives', 'Active Cameras'), value: this.kpisData[3].value, icon: 'videocam', color: 'red', iconColor: '#f44336', trend: this.kpisData[3].trend }
    ];
  }

  kpisData = [
    { value: '--', trend: '0' },
    { value: '--', trend: '0' },
    { value: '--', trend: '0' },
    { value: '--', trend: '0' }
  ];

  aiInsights: string[] = [];
  attendanceData: any[] = [];
  alerts: any[] = [];
  cameraActivity: any[] = [];

  // Stable cache: camera detections don't reset between polling cycles
  private cameraDetectionsCache: Map<string, number> = new Map();

  // Attendance filtré (seulement employés encore actifs — sans les supprimés)
  private filteredAttendance: any[] = [];

  colorLegend = [
    { name: 'RED', color: '#f44336' },
    { name: 'BLUE', color: '#2196f3' },
    { name: 'YELLOW', color: '#ffeb3b' },
    { name: 'OTHER', color: '#9e9e9e' }
  ];

  constructor(private analyticsService: AnalyticsService, public langService: LanguageService) { }

  ngOnInit(): void {
    this.fetchDataWithPolling();
  }

  ngOnDestroy() {
    if (this.dataSubscription) {
      this.dataSubscription.unsubscribe();
    }
  }

  fetchDataWithPolling() {
    this.dataSubscription = this.analyticsService.getDashboardDataWithPolling(10000).subscribe({
      next: (data) => {
        this.error = false;
        this.processData(data);
        this.loading = false;
        this.lastUpdated = new Date().toLocaleTimeString();
        // Rebuild charts after data is processed (300ms lets Angular finish rendering)
        setTimeout(() => {
          this.initPresenceChart(this.filteredAttendance);
          this.initColorChart(this.filteredAttendance);
        }, 300);
      },
      error: (err) => {
        console.error('Erreur analytics:', err);
        this.error = true;
        this.loading = false;
      }
    });
  }

  processData(data: any) {
    const attendance: any[] = Array.isArray(data.attendance) ? data.attendance : [];
    const employees: any[] = Array.isArray(data.employees) ? data.employees : [];
    const cameras: any[] = Array.isArray(data.cameras) ? data.cameras : [];
    const alerts: any[] = Array.isArray(data.alerts) ? data.alerts : [];

    // Exclude attendance records from deleted employees — match by name against current employees list
    const currentEmployeeNames = new Set(
      employees.map((e: any) => (e.name || '').toLowerCase().trim())
    );
    const filteredAttendance = attendance.filter((a: any) => {
      if (a.unknown === true) return true;
      const empName = (a.employeeName || '').toLowerCase().trim();
      return empName === '' || empName === 'unknown' || currentEmployeeNames.has(empName);
    });
    this.filteredAttendance = filteredAttendance;

    // KPI 1: unique employees with at least one IN event today
    const today = new Date().toISOString().split('T')[0];
    const todayRecords = filteredAttendance.filter((a: any) => {
      if (!a.timestamp) return false;
      let d: Date;
      if (Array.isArray(a.timestamp)) {
        d = new Date(a.timestamp[0], a.timestamp[1] - 1, a.timestamp[2]);
      } else {
        d = new Date(a.timestamp);
      }
      return d.toISOString().split('T')[0] === today;
    });
    const presentNames = new Set(
      todayRecords
        .filter((a: any) => a.status === 'IN')
        .map((a: any) => (a.employeeName || '').toLowerCase().trim())
        .filter((n: string) => n !== '')
    );
    const presentCount = presentNames.size;
    const totalEmp = employees.length || 1;
    this.kpisData[0].value = presentCount.toString();
    this.kpisData[0].trend = ((presentCount / totalEmp) * 100).toFixed(0);

    // KPI 2: hours worked — computed from IN/OUT pairs per employee
    let totalHours = 0;
    const byEmployee: Map<string, any[]> = new Map();
    filteredAttendance.forEach((a: any) => {
      const name = a.employeeName || 'unknown';
      if (!byEmployee.has(name)) byEmployee.set(name, []);
      byEmployee.get(name)!.push(a);
    });
    byEmployee.forEach(records => {
      const ins = records.filter(r => r.status === 'IN').sort((a, b) => +new Date(a.timestamp) - +new Date(b.timestamp));
      const outs = records.filter(r => r.status === 'OUT').sort((a, b) => +new Date(a.timestamp) - +new Date(b.timestamp));
      for (let i = 0; i < Math.min(ins.length, outs.length); i++) {
        const diff = (new Date(outs[i].timestamp).getTime() - new Date(ins[i].timestamp).getTime()) / 3600000;
        if (diff > 0 && diff < 16) totalHours += diff;
      }
    });
    this.kpisData[1].value = totalHours > 0 ? `${totalHours.toFixed(1)}h` : '0h';
    this.kpisData[1].trend = '0';

    // KPI 3: total IN events today
    const todayEntries = todayRecords.filter((a: any) => a.status === 'IN').length;
    this.kpisData[2].value = todayEntries.toString();
    this.kpisData[2].trend = '0';

    // KPI 4: active cameras / total
    const activeCams = cameras.filter(c => c.status === 'ACTIVE').length;
    this.kpisData[3].value = `${activeCams}/${cameras.length}`;
    this.kpisData[3].trend = '0';

    const highAlerts = alerts.filter(a => (a.severity || a.level || '').toUpperCase() === 'HIGH').length;
    const zones = new Set(cameras.map(c => c.location)).size;
    const unknownCount = filteredAttendance.filter((a: any) => a.unknown === true || a.employeeName === 'UNKNOWN').length;
    this.aiInsights = [
      this.langService.t(
        `✅ ${presentCount} employé(s) actuellement détecté(s) sur ${totalEmp} enregistrés.`,
        `✅ ${presentCount} employee(s) currently detected out of ${totalEmp} registered.`
      ),
      this.langService.t(
        `⚠️ ${highAlerts} alerte(s) critique(s) nécessitant une attention immédiate.`,
        `⚠️ ${highAlerts} critical alert(s) requiring immediate attention.`
      ),
      this.langService.t(
        `📷 ${cameras.length} caméra(s) surveillant ${zones} zone(s).`,
        `📷 ${cameras.length} camera(s) monitoring ${zones} zone(s).`
      ),
      unknownCount > 0
        ? this.langService.t(`🚨 ${unknownCount} personne(s) inconnue(s) détectée(s) aujourd'hui.`, `🚨 ${unknownCount} unknown person(s) detected today.`)
        : this.langService.t(`💡 Aucune intrusion détectée aujourd'hui.`, `💡 No intrusions detected today.`)
    ];

    this.attendanceData = filteredAttendance.slice(-8).map((a: any) => ({
      name: a.employeeName || 'Unknown',
      date: a.timestamp ? new Date(a.timestamp).toLocaleDateString() : '--',
      in: a.status === 'IN' && a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : (a.timeIn || '--'),
      out: a.status === 'OUT' && a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : (a.timeOut || '--'),
      status: a.status === 'IN' ? 'PRESENT' : (a.status === 'OUT' ? 'FINISHED' : (a.timeOut ? 'FINISHED' : 'PRESENT')),
      unknown: a.unknown
    })).reverse();

    this.alerts = alerts.slice(-3).map(a => ({
      title: a.type ? a.type.replace(/_/g, ' ') : 'Security Alert',
      message: a.message || '',
      time: a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : '--',
      location: a.location || (a.cameraId ? `Camera ${a.cameraId}` : 'Inconnue'),
      level: (a.severity || a.level || 'MEDIUM').toLowerCase(),
      confidence: a.confidence || 85
    })).reverse();

    this.cameraActivity = cameras.map(c => {
      const camKey = c.name || String(c.id);
      const isActive = (c.status || '').toUpperCase() === 'ACTIVE';
      const existingDetections = this.cameraDetectionsCache.get(camKey) || 0;
      const detected = attendance.filter(a => String(a.cameraId) === String(c.id)).length;
      const stableDetections = Math.max(existingDetections, detected);
      this.cameraDetectionsCache.set(camKey, stableDetections);
      return {
        name: c.name || `Camera ${c.id}`,
        location: c.location || '',
        detections: stableDetections,
        activity: isActive ? 80 : 0,
        online: isActive
      };
    });

    const activeCamsCount = cameras.filter(c => (c.status || '').toUpperCase() === 'ACTIVE').length;
    this.kpisData[3].value = `${activeCamsCount}/${cameras.length}`;
  }

  initPresenceChart(attendance: any[]) {
    try {
      if (this.presenceChartInstance) {
        this.presenceChartInstance.detach();
        this.presenceChartInstance = null;
      }

      const hoursLabels = ['08h', '10h', '12h', '14h', '16h', '18h', '20h', '22h'];
      const counts = [0, 0, 0, 0, 0, 0, 0, 0];

      attendance.forEach(a => {
        if (a.timestamp) {
          let date: Date;
          if (Array.isArray(a.timestamp)) {
            date = new Date(a.timestamp[0], a.timestamp[1]-1, a.timestamp[2], a.timestamp[3]||0, a.timestamp[4]||0);
          } else {
            date = new Date(a.timestamp);
          }
          const hour = date.getHours();
          if (hour >= 8 && hour <= 22) {
            const idx = Math.floor((hour - 8) / 2);
            if (idx >= 0 && idx < counts.length) {
              counts[idx]++;
            }
          }
        }
      });

      // Utiliser les données réelles uniquement (zéros si pas d'activité)
      const series = [counts];

      const dataPresenceChart: any = {
        labels: hoursLabels,
        series: series
      };

      const optionsPresenceChart: any = {
        lineSmooth: Chartist.Interpolation.cardinal({ tension: 0.4 }),
        low: 0,
        showArea: true,
        chartPadding: { top: 20, right: 20, bottom: 10, left: 10 },
        axisY: { onlyInteger: true }
      };

      const el = document.getElementById('presenceChart');
      if (el) {
        this.presenceChartInstance = new Chartist.Line('#presenceChart', dataPresenceChart, optionsPresenceChart);
      }
    } catch (e) {
      console.warn('Chartist presenceChart error:', e);
    }
  }

  initColorChart(attendance?: any[]) {
    try {
      if (this.colorChartInstance) {
        this.colorChartInstance.detach();
        this.colorChartInstance = null;
      }

      // Compter les couleurs depuis les données ou utiliser une répartition par défaut stable
      let red = 0, blue = 0, yellow = 0, other = 0;
      if (attendance && attendance.length > 0) {
        attendance.forEach(a => {
          const color = (a.clothingColor || a.detectedColor || '').toUpperCase();
          if (color.includes('RED')) red++;
          else if (color.includes('BLUE')) blue++;
          else if (color.includes('YELLOW') || color.includes('GREEN')) yellow++;
          else other++;
        });
      }
      // Fallback si pas de données couleur
      if (red + blue + yellow + other === 0) {
        red = 45; blue = 25; yellow = 20; other = 10;
      }

      const dataColorChart = {
        series: [red, blue, yellow, other]
      };

      const optionsColorChart = {
        donut: true,
        donutWidth: 30,
        startAngle: 270,
        showLabel: false
      };

      const el = document.getElementById('colorChart');
      if (el) {
        this.colorChartInstance = new Chartist.Pie('#colorChart', dataColorChart, optionsColorChart);
      }
    } catch (e) {
      console.warn('Chartist colorChart error:', e);
    }
  }
}
