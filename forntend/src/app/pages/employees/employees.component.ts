import { Component, OnInit } from '@angular/core';
import { EmployeeService, Employee } from '../../services/employee.service';

@Component({
  selector: 'app-employees',
  templateUrl: './employees.component.html',
  styleUrls: ['./employees.component.scss']
})
export class EmployeesComponent implements OnInit {

  employees: Employee[] = [];
  jobs = [
    { value: 'DOCTOR', label: 'Vétérinaire' },
    { value: 'ELECTRICIAN', label: 'Technicien Électrique' },
    { value: 'WORKER', label: 'Ouvrier Agricole' }
  ];

  form: any = { name: '', email: '', phone: '', job: '', department: null };
  submitted = false;

  showToast = false;
  toastMessage = '';
  toastType: 'success' | 'error' = 'success';
  private toastTimer: any;

  isDarkMode = true;

  private readonly emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  constructor(private service: EmployeeService) { }

  ngOnInit(): void {
    this.applyTheme();
    this.load();
  }

  load() {
    this.service.getEmployees().subscribe({
      next: res => this.employees = res,
      error: () => this.toast('Erreur lors du chargement.', 'error')
    });
  }

  get nameValid(): boolean {
    return this.form.name?.trim().length > 0;
  }

  get emailValid(): boolean {
    if (!this.form.email) return true;
    return this.emailRegex.test(this.form.email);
  }

  get formValid(): boolean {
    return this.nameValid && this.emailValid && !!this.form.job;
  }

  save() {
    this.submitted = true;
    if (!this.formValid) return;

    const payload: Employee = {
      name: this.form.name.trim(),
      email: this.form.email || '',
      phone: this.form.phone || '',
      job: this.form.job,
      status: 'PENDING',
      faceRegistered: false
    };

    this.service.create(payload).subscribe({
      next: () => {
        this.toast('Employé ajouté avec succès ✅', 'success');
        this.load();
        this.form = { name: '', email: '', phone: '', job: '', department: null };
        this.submitted = false;
      },
      error: () => this.toast("Erreur lors de l'ajout.", 'error')
    });
  }

  delete(id?: number) {
    if (!id) return;
    if (!confirm('Supprimer cet employé ?')) return;

    this.service.delete(id).subscribe({
      next: () => {
        this.toast('Employé supprimé.', 'success');
        this.load();
      },
      error: () => this.toast('Erreur lors de la suppression.', 'error')
    });
  }

  approve(id?: number) {
    if (!id) return;

    this.service.approve(id).subscribe({
      next: () => {
        this.toast('Employé approuvé avec succès ✅', 'success');
        this.load();
      },
      error: () => this.toast('Erreur lors de l\'approbation.', 'error')
    });
  }

  validateFace(id?: number) {
    if (!id) return;

    this.service.validateFace(id).subscribe({
      next: () => {
        this.toast('Visage validé ✅', 'success');
        this.load();
      },
      error: () => this.toast('Erreur lors de la validation.', 'error')
    });
  }

  toggleDarkMode() {
    this.isDarkMode = !this.isDarkMode;
    this.applyTheme();
  }

  private applyTheme() {
    if (this.isDarkMode) {
      document.body.classList.remove('light-mode');
    } else {
      document.body.classList.add('light-mode');
    }
  }

  private toast(message: string, type: 'success' | 'error') {
    clearTimeout(this.toastTimer);
    this.toastMessage = message;
    this.toastType = type;
    this.showToast = true;
    this.toastTimer = setTimeout(() => this.showToast = false, 3000);
  }
}
