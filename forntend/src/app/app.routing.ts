import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { AdminLayoutComponent } from './layouts/admin-layout/admin-layout.component';
import { LoginComponent } from './login/login.component';
import { DepartmentsComponent } from './departments/departments.component';
import { ManagersComponent } from './managers/managers.component';
import { ViewersComponent } from './viewers/viewers.component';
import { CamerasComponent } from './cameras/cameras.component';
import { AlertsComponent } from './alerts/alerts.component';
import { UserProfileComponent } from './user-profile/user-profile.component';
import { AuthGuard } from './guards/auth.guard';

import { EmployeesComponent } from './pages/employees/employees.component';
import { FaceRegistrationComponent } from './pages/face-registration/face-registration.component';
import { AnalyticsComponent } from './analytics/analytics.component';
import { ActivateComponent } from './pages/activate/activate.component';
import { FaceSetupComponent } from './pages/face-setup/face-setup.component';
import { ManagerDashboardComponent } from './manager-dashboard/manager-dashboard.component';
import { ViewerDashboardComponent } from './viewer-dashboard/viewer-dashboard.component';
import { SettingsComponent } from './settings/settings.component';

const routes: Routes = [

  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'activate', component: ActivateComponent },
  { path: 'face-setup', component: FaceSetupComponent },

  {
    path: 'dashboard/manager',
    component: ManagerDashboardComponent,
    canActivate: [AuthGuard],
    data: { role: 'ROLE_MANAGER' }
  },
  {
    path: 'dashboard/viewer',
    component: ViewerDashboardComponent,
    canActivate: [AuthGuard],
    data: { role: 'ROLE_VIEWER' }
  },

  {
    path: 'dashboard',
    component: AdminLayoutComponent,
    canActivate: [AuthGuard],
    data: { role: 'ROLE_ADMIN' },
    children: [
      { path: 'departments', component: DepartmentsComponent },
      { path: 'managers', component: ManagersComponent },
      { path: 'viewers', component: ViewersComponent },
      { path: 'cameras', component: CamerasComponent },
      { path: 'alerts', component: AlertsComponent },
      { path: 'employees', component: EmployeesComponent },
      { path: 'face-registration', component: FaceRegistrationComponent },
      { path: 'settings', component: SettingsComponent },
      { path: 'user-profile', component: UserProfileComponent },
      { path: 'analytics', component: AnalyticsComponent },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' }
    ]
  },

  { path: '**', redirectTo: 'login' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes, { useHash: true })],
  exports: [RouterModule]
})
export class AppRoutingModule {}
