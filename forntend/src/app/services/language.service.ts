import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LanguageService {
  private currentLang = new BehaviorSubject<string>(localStorage.getItem('lang') || 'fr');
  currentLang$ = this.currentLang.asObservable();

  get lang() {
    return this.currentLang.value;
  }

  toggleLanguage() {
    const newLang = this.lang === 'fr' ? 'en' : 'fr';
    localStorage.setItem('lang', newLang);
    this.currentLang.next(newLang);
  }

  t(fr: string, en: string): string {
    return this.lang === 'fr' ? fr : en;
  }
}
