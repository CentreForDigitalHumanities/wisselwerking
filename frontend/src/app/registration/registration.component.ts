import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { faTimes, faChevronUp, faChevronDown } from '@fortawesome/free-solid-svg-icons';
import { ExchangeSession } from '../models';
import { RegistrationService } from '../services/registration.service';

@Component({
    selector: 'wsl-registration',
    standalone: true,
    imports: [CommonModule, FontAwesomeModule, FormsModule],
    templateUrl: './registration.component.html',
    styleUrl: './registration.component.scss'
})
export class RegistrationComponent {
    faTimes = faTimes;
    faChevronUp = faChevronUp;
    faChevronDown = faChevronDown;
    sessions$ = this.registrationService.sessions$;
    sessionPriorities$ = this.registrationService.sessionPriorities$;
    departments$ = this.registrationService.departments();
    selectedSession = 0;

    constructor(private registrationService: RegistrationService) {

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
