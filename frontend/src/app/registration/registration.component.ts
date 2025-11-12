import { Component, Inject, LOCALE_ID, OnDestroy } from '@angular/core';
import { FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
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
    error = '';

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

    private additionalValidation(): boolean {
        this.choiceInvalid = this.sessionPriorities.length === 0;

        if (this.registration.department === '---' ||
            this.registration.department === 'anders' && !(this.departmentOther ?? '').trim()) {
            this.departmentInvalid = true;
            return false;
        }
        this.departmentInvalid = false;

        if (this.choiceInvalid || this.departmentInvalid) {
            return false;
        }

        return true;
    }

    async submit() {
        if (!this.additionalValidation()) {
            return;
        }

        this.submitting = true;

        const data = {
            language: this.currentLanguage,
            ...this.registration,
            // remove some unneeded data
            sessionPriorities: this.sessionPriorities.map(
                sp => ({
                    ...sp,
                    session: {
                        ...sp.session,
                        organizers: [],
                        descriptions: []
                    }
                })
            ),
            department: this.registration.department === 'anders'
                ? this.departmentOther
                : this.registration.department
        };

        try {

            await this.registrationService.register(data);

            this.thankYou = true;
        }
        catch (err: any) {
            this.error = `Something went wrong during the registration.
Please try again and notify wisselwerking.gw@uu.nl with the following information if this persists.

Error details:
${err['message'] ?? err}

Your data:
${JSON.stringify(data, null, 4)}`;
            this.submitting = false;
        }
    }

    checkValidation(formGroup: FormGroup) {
        for (const control of Object.values(formGroup.controls)) {
            control.markAsDirty();
        }
        return this.additionalValidation();
    }
}
