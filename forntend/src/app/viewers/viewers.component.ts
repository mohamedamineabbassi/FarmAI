import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { UserService, User } from '../services/user.service';

@Component({
  selector: 'app-viewers',
  templateUrl: './viewers.component.html',
  styleUrls: ['./viewers.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class ViewersComponent implements OnInit {

  viewers: User[] = [];
  viewer: User = this.resetForm();

  editMode = false;
  editId: number | null = null;
  loading = false;

  constructor(private service: UserService) {}

  ngOnInit(): void {
    this.load();
  }

  load() {
    this.loading = true;

    this.service.getViewers().subscribe({
      next: (res) => {
        this.viewers = res;
        this.loading = false;
      },
      error: (err) => {
        console.error(err);
        alert("Erreur chargement ❌");
        this.loading = false;
      }
    });
  }

  save() {

    if (!this.viewer.email) {
      alert("Email obligatoire ❌");
      return;
    }

    if (this.editMode && this.editId !== null) {

      this.service.update(this.editId, this.viewer).subscribe({
        next: () => {

          const index = this.viewers.findIndex(v => v.id === this.editId);

          if (index !== -1) {
            this.viewers[index] = {
              ...this.viewer,
              id: this.editId
            };
          }

          alert("Viewer mis à jour ✅");
          this.reset();
        },
        error: (err) => {
          console.error(err);
          alert("Erreur update ❌");
        }
      });

    } else {

      this.service.createViewer(this.viewer).subscribe({
        next: (newViewer: User) => {
          this.viewers.unshift(newViewer);
          alert("Viewer créé + email envoyé ✅");
          this.reset();
        },
        error: (err) => {

          console.error(err);

          if (err.status === 400 || err.status === 500) {
            alert("Email déjà utilisé ❌");
          } else if (err.status === 403) {
            alert("Accès refusé (token ou rôle) ❌");
          } else {
            alert("Erreur création ❌");
          }
        }
      });

    }
  }

  edit(v: User) {
    this.viewer = { ...v };
    this.editMode = true;
    this.editId = v.id!;
  }

  delete(id: number) {

    if (!id) return;

    if (confirm("Supprimer ce viewer ?")) {

      this.service.delete(id).subscribe({
        next: () => {
          this.viewers = this.viewers.filter(v => v.id !== id);
          alert("Viewer supprimé ✅");
        },
        error: (err) => {
          console.error(err);

          if (err.status === 403) {
            alert("Accès refusé ❌");
          } else {
            alert("Erreur suppression ❌");
          }
        }
      });

    }
  }

  reset() {
    this.viewer = this.resetForm();
    this.editMode = false;
    this.editId = null;
  }

  resetForm(): User {
    return {
      firstName: '',
      lastName: '',
      email: '',
      phone: ''
    };
  }
}
