import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { RouterModule } from '@angular/router';

// Routing
import { AppRoutingModule } from './app.routing';

// Components module (UI)
import { ComponentsModule } from './components/components.module';

// Components
import { AppComponent } from './app.component';
import { AdminLayoutComponent } from './layouts/admin-layout/admin-layout.component';
import { LoginComponent } from './login/login.component';
import { DepartmentsComponent } from './departments/departments.component';
import { ManagersComponent } from './managers/managers.component';
import { ViewersComponent } from './viewers/viewers.component';
import { CamerasComponent } from './cameras/cameras.component';
import { AlertsComponent } from './alerts/alerts.component';

// Interceptors
import { AuthInterceptor } from './services/auth.interceptor';
import { TokenErrorInterceptor } from './services/token-error.interceptor';
import { EmployeesComponent } from './pages/employees/employees.component';
import { FaceRegistrationComponent } from './pages/face-registration/face-registration.component';
import { ActivateComponent } from './pages/activate/activate.component';
import { FaceSetupComponent } from './pages/face-setup/face-setup.component';
import { ManagerDashboardComponent } from './manager-dashboard/manager-dashboard.component';
import { ViewerDashboardComponent } from './viewer-dashboard/viewer-dashboard.component';
import { SettingsComponent } from './settings/settings.component';
import { UserProfileComponent } from './user-profile/user-profile.component';
import { AttendanceComponent } from './attendance/attendance.component';
import { WelcomeComponent } from './welcome/welcome.component';
import { FaceIdAttendanceComponent } from './faceid-attendance/faceid-attendance.component';

@NgModule({
  declarations: [
    AppComponent,
    AdminLayoutComponent,
    LoginComponent,
    DepartmentsComponent,
    ManagersComponent,
    ViewersComponent,
    CamerasComponent,
    AlertsComponent,
    EmployeesComponent,
    FaceRegistrationComponent,
    ActivateComponent,
    FaceSetupComponent,
    ManagerDashboardComponent,
    ViewerDashboardComponent,
    SettingsComponent,
    UserProfileComponent,
    AttendanceComponent,
    WelcomeComponent,
    FaceIdAttendanceComponent
  ],

  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    FormsModule,
    ReactiveFormsModule,
    HttpClientModule,
    ComponentsModule,
    RouterModule,
    AppRoutingModule
  ],

  providers: [
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,      // 1) Ajoute le token Authorization
      multi: true
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: TokenErrorInterceptor, // 2) Gère les 401 (session expirée → login)
      multi: true
    }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
