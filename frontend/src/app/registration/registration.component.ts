import { Component, Inject, LOCALE_ID, OnDestroy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { TranslateDirective, TranslatePipe } from '@ngx-translate/core';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { faTimes, faChevronUp, faChevronDown } from '@fortawesome/free-solid-svg-icons';
import { ExchangeSession, Language } from '../models';
import { RegistrationService } from '../services/registration.service';
import { LanguageService } from '../services/language.service';

@Component({
    selector: 'wsl-registration',
    standalone: true,
    imports: [CommonModule, FontAwesomeModule, FormsModule, TranslatePipe, TranslateDirective],
    templateUrl: './registration.component.html',
    styleUrl: './registration.component.scss'
})
export class RegistrationComponent implements OnDestroy {
    private subscription: Subscription;

    faTimes = faTimes;
    faChevronUp = faChevronUp;
    faChevronDown = faChevronDown;
    currentLanguage: string;
    sessions$ = this.registrationService.sessions$;
    sessionPriorities$ = this.registrationService.sessionPriorities$;
    departments$ = this.registrationService.departments();
    selectedSession = 0;

    registration = {
        firstName: '',
        tussenvoegsel: '',
        lastName: '',
        department: '---',
        email: '',
        notes: '',
        reason: ''
    };

    constructor(private registrationService: RegistrationService,
        private languageService: LanguageService,
        @Inject(LOCALE_ID) private localeId: string) {
        this.currentLanguage = this.localeId;
        this.subscription = this.languageService.current$.subscribe(language => this.currentLanguage = language);
        this.initLanguage();
    }

    ngOnDestroy(): void {
        this.subscription.unsubscribe();
    }

    private async initLanguage() {
        const languageInfo = await this.languageService.get();
        this.currentLanguage = languageInfo.current || this.localeId;
    }

    setLanguage(language: Language) {
        this.languageService.set(language);
    }

    updatePriority(session: ExchangeSession['pk'], priority: number) {
        this.registrationService.updatePriority(session, priority);
    }

    add() {
        this.registrationService.update(this.selectedSession, true);
    }

    remove(sessionPk: number) {
        this.registrationService.update(sessionPk, false);
    }
}
