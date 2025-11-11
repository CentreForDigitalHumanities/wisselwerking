import { Component, Inject, LOCALE_ID, OnDestroy } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { TranslateDirective, TranslatePipe } from '@ngx-translate/core';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { faTimes, faChevronUp, faChevronDown } from '@fortawesome/free-solid-svg-icons';
import { ExchangeSession, Language } from '../models';
import { ExchangeSessionPriority, RegistrationService } from '../services/registration.service';
import { LanguageService } from '../services/language.service';
import { ThankYouComponent } from "../thank-you/thank-you.component";

@Component({
    selector: 'wsl-registration',
    standalone: true,
    imports: [CommonModule, FontAwesomeModule, FormsModule, TranslatePipe, TranslateDirective, ReactiveFormsModule, ThankYouComponent],
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
    departmentOther = '';
    choiceInvalid = false;
    departmentInvalid = false;
    submitting = false;
    thankYou = false;

    registration = {
        firstName: '',
        tussenvoegsel: '',
        lastName: '',
        department: 'anders', // TODO: have a selection
        email: '',
        notes: '',
        reason: ''
    };

    private sessionPriorities: ExchangeSessionPriority[] = [];

    constructor(private registrationService: RegistrationService,
        private languageService: LanguageService,
        @Inject(LOCALE_ID) private localeId: string) {
        this.currentLanguage = this.localeId;
        this.subscription = this.languageService.current$.subscribe(language => this.currentLanguage = language);
        this.subscription.add(
            this.registrationService.sessionPriorities$.subscribe(s => {
                this.sessionPriorities = s;
            })
        );
    }

    ngOnDestroy(): void {
        this.subscription.unsubscribe();
    }

    setLanguage(language: Language) {
        this.languageService.set(language);
    }

    updatePriority(session: ExchangeSession['pk'], priority: number) {
        this.registrationService.updatePriority(session, priority);
    }

    add() {
        this.choiceInvalid = false;
        this.registrationService.update(this.selectedSession, true);
    }

    remove(sessionPk: number) {
        this.registrationService.update(sessionPk, false);
    }

    async submit() {
        this.choiceInvalid = this.sessionPriorities.length === 0;

        if (this.registration.department === '---' ||
            this.registration.department === 'anders' && !(this.departmentOther ?? '').trim()) {
            this.departmentInvalid = true;
            return;
        }
        this.departmentInvalid = false;

        if (this.choiceInvalid || this.departmentInvalid) {
            return;
        }

        this.submitting = true;

        await this.registrationService.register({
            language: this.currentLanguage,
            ...this.registration,
            sessionPriorities: this.sessionPriorities,
            department: this.registration.department === 'anders'
                ? this.departmentOther
                : this.registration.department
        });

        this.thankYou = true;
    }
}
