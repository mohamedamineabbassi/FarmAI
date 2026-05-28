import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { DepartmentService } from '../services/department.service';
import { ManagerService } from '../services/manager.service';

@Component({
  selector: 'app-departments',
  templateUrl: './departments.component.html',
  styleUrls: ['./departments.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class DepartmentsComponent implements OnInit {

  departments: any[] = [];
  managers: any[] = [];

  department: any = this.resetForm();

  editMode = false;
  editId: number | null = null;

  saving   = false;
  successMsg = '';
  errorMsg   = '';

  constructor(
    private service: DepartmentService,
    private managerService: ManagerService
  ) { }

  ngOnInit(): void {
    this.loadDepartments();
    this.loadManagers();
  }

  loadDepartments() {
    this.service.getDepartments().subscribe({
      next: (res) => this.departments = res,
      error: () => this.showError('Impossible de charger les départements.')
    });
  }

  loadManagers() {
    this.managerService.getManagers().subscribe({
      next:  (res) => this.managers = res,
      error: ()    => {}
    });
  }

  save() {

    if (!this.department.manager?.id) {
      this.showError('Veuillez sélectionner un responsable.');
      return;
    }

    this.department.doctors      = Number(this.department.doctors      || 0);
    this.department.electricians = Number(this.department.electricians || 0);
    this.department.workers      = Number(this.department.workers      || 0);

    if (this.department.doctors < 0 || this.department.electricians < 0 || this.department.workers < 0) {
      this.showError('Les effectifs doivent être des nombres positifs.');
      return;
    }

    if (!this.department.startTime || !this.department.endTime) {
      this.showError('Veuillez saisir les horaires de travail.');
      return;
    }

    const payload = {
      ...this.department,
      startTime: this.department.startTime + ':00',
      endTime:   this.department.endTime   + ':00'
    };

    this.saving     = true;
    this.successMsg = '';
    this.errorMsg   = '';

    if (this.editMode) {
      this.service.update(this.editId!, payload).subscribe({
        next: () => {
          this.showSuccess('Département mis à jour avec succès ✅');
          this.loadDepartments();
          this.reset();
          this.saving = false;
        },
        error: (err) => {
          this.saving = false;
          this.showError(this.extractError(err, 'Erreur lors de la mise à jour.'));
        }
      });
    } else {
      this.service.create(payload).subscribe({
        next: () => {
          this.showSuccess('Département créé avec succès ✅');
          this.loadDepartments();
          this.reset();
          this.saving = false;
        },
        error: (err) => {
          this.saving = false;
          this.showError(this.extractError(err, 'Erreur lors de la création.'));
        }
      });
    }
  }

  edit(dep: any) {
    this.successMsg = '';
    this.errorMsg   = '';
    this.department = {
      ...dep,
      manager:      { id: dep.manager?.id },
      startTime:    dep.startTime?.substring(0, 5),
      endTime:      dep.endTime?.substring(0, 5),
      doctors:      Number(dep.doctors      || 0),
      electricians: Number(dep.electricians || 0),
      workers:      Number(dep.workers      || 0)
    };
    this.editMode = true;
    this.editId   = dep.id;
  }

  delete(id: number) {
    if (confirm('Supprimer ce département ?')) {
      this.service.delete(id).subscribe({
        next: () => {
          this.showSuccess('Département supprimé.');
          this.loadDepartments();
        },
        error: (err) => this.showError(this.extractError(err, 'Erreur lors de la suppression.'))
      });
    }
  }

  reset() {
    this.department = this.resetForm();
    this.editMode   = false;
    this.editId     = null;
    this.successMsg = '';
    this.errorMsg   = '';
  }

  resetForm() {
    return {
      name:         '',
      startTime:    '',
      endTime:      '',
      doctors:      0,
      electricians: 0,
      workers:      0,
      manager:      { id: null }
    };
  }

  getRequiredTotal(dep: any = this.department): number {
    return Number(dep.doctors || 0) + Number(dep.electricians || 0) + Number(dep.workers || 0);
  }

  private showSuccess(msg: string) {
    this.successMsg = msg;
    this.errorMsg   = '';
    setTimeout(() => this.successMsg = '', 4000);
  }

  private showError(msg: string) {
    this.errorMsg   = msg;
    this.successMsg = '';
  }

  private extractError(err: any, fallback: string): string {
    if (err?.error?.error)   return err.error.error;
    if (err?.error?.message) return err.error.message;
    if (err?.status === 401) return '⏱️ Session expirée — veuillez vous reconnecter.';
    if (err?.status === 403) return '🔒 Accès refusé — permission insuffisante. Veuillez vous reconnecter et réessayer.';
    return fallback;
  }
}
