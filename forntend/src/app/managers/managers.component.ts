import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { ManagerService, Manager } from '../services/manager.service';

@Component({
  selector: 'app-managers',
  templateUrl: './managers.component.html',
  styleUrls: ['./managers.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class ManagersComponent implements OnInit {

  managers: Manager[] = [];
  manager: Manager    = this.resetForm();

  isEdit   = false;
  loading  = false;
  saving   = false;

  successMsg = '';
  errorMsg   = '';

  constructor(private service: ManagerService) {}

  ngOnInit(): void {
    this.loadManagers();
  }

  loadManagers() {
    this.loading = true;
    this.service.getManagers().subscribe({
      next:  (res) => { this.managers = res; this.loading = false; },
      error: (err) => {
        console.error(err);
        this.loading = false;
        this.showError('Impossible de charger les gestionnaires.');
      }
    });
  }

  save() {
    this.clearMessages();

    if (!this.manager.firstName?.trim()) {
      this.showError('Le prénom est obligatoire.');
      return;
    }
    if (!this.manager.email?.trim()) {
      this.showError("L'adresse email est obligatoire.");
      return;
    }

    this.saving = true;

    if (this.isEdit && this.manager.id) {
      this.service.update(this.manager.id, this.manager).subscribe({
        next: () => {
          this.saving = false;
          this.showSuccess('Gestionnaire modifié avec succès ✅');
          this.afterSave();
        },
        error: (err) => {
          this.saving = false;
          this.showError(this.extractError(err, 'Erreur lors de la modification.'));
        }
      });
    } else {
      this.service.create(this.manager).subscribe({
        next: () => {
          this.saving = false;
          this.showSuccess('Gestionnaire créé ! Un email d\'activation a été envoyé. ✅');
          this.afterSave();
        },
        error: (err) => {
          this.saving = false;
          this.showError(this.extractError(err, 'Erreur lors de la création.'));
        }
      });
    }
  }

  edit(m: Manager) {
    this.manager = { ...m };
    this.isEdit  = true;
    this.clearMessages();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  delete(id: number) {
    if (!confirm('Supprimer ce gestionnaire ?')) return;
    this.service.delete(id).subscribe({
      next:  () => { this.showSuccess('Gestionnaire supprimé.'); this.loadManagers(); },
      error: (err) => { this.showError(this.extractError(err, 'Erreur lors de la suppression.')); }
    });
  }

  private extractError(err: any, fallback: string): string {
    if (err?.error?.error)   return err.error.error;
    if (err?.error?.message) return err.error.message;
    if (err?.status === 403) return 'Permission refusée. Seul un administrateur peut effectuer cette action.';
    if (err?.status === 409) return 'Cet email est déjà utilisé par un autre compte.';
    return fallback;
  }

  private showSuccess(msg: string) {
    this.successMsg = msg;
    this.errorMsg   = '';
    setTimeout(() => this.successMsg = '', 5000);
  }

  private showError(msg: string) {
    this.errorMsg   = msg;
    this.successMsg = '';
  }

  private clearMessages() {
    this.successMsg = '';
    this.errorMsg   = '';
  }

  resetForm(): Manager {
    return { firstName: '', lastName: '', email: '', phone: '' };
  }

  afterSave() {
    this.manager = this.resetForm();
    this.isEdit  = false;
    this.loadManagers();
  }
}
