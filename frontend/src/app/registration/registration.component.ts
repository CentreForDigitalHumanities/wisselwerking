import { Component } from '@angular/core';
import { ExchangeSessionPriority, RegistrationService } from '../services/registration.service';
import { CommonModule } from '@angular/common';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { fa1, fa2, fa3, fa4, faTimes } from '@fortawesome/free-solid-svg-icons';
import { ExchangeSession } from '../models';

@Component({
    selector: 'wsl-registration',
    standalone: true,
    imports: [CommonModule, FontAwesomeModule],
    templateUrl: './registration.component.html',
    styleUrl: './registration.component.scss'
})
export class RegistrationComponent {
    priorityIcons = {
        1: fa1,
        2: fa2,
        3: fa3,
        4: fa4
    };

    faTimes = faTimes;
    sessions$ = this.registrationService.sessions$;
    sessionPriorities$ = this.registrationService.sessionPriorities$;
    departments$ = this.registrationService.departments();

    constructor(private registrationService: RegistrationService) {

    }

    updatePriority(session: ExchangeSession['pk'], priority: number) {
        this.registrationService.updatePriority(session, priority - 1);
    }
}
