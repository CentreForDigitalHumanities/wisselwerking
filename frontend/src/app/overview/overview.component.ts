import { Component, OnDestroy, OnInit, QueryList, ViewChildren } from '@angular/core';
import { BackendService } from '../services/backend.service';
import { ExchangeSessionComponent } from "../exchange-session/exchange-session.component";
import { ExchangeSession } from '../models';
import { faCheck, faCircleChevronUp } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { RegistrationService } from '../services/registration.service';
import { Subscription } from 'rxjs';

@Component({
    selector: 'wsl-overview',
    templateUrl: './overview.component.html',
    styleUrls: ['./overview.component.scss'],
    standalone: true,
    imports: [CommonModule, FontAwesomeModule, RouterLink, ExchangeSessionComponent]
})
export class OverviewComponent implements OnDestroy {
    subscriptions = new Subscription();

    faCheck = faCheck;
    faCircleChevronUp = faCircleChevronUp;
    interested: { [pk: ExchangeSession['pk']]: boolean } = {};
    interestedList: ExchangeSession[] = [];

    sessions?: ExchangeSession[];

    @ViewChildren(ExchangeSessionComponent)
    sessionElements?: QueryList<ExchangeSessionComponent>;

    constructor(private backend: BackendService, private registrationService: RegistrationService) {
        this.subscriptions.add(registrationService.interested$.subscribe(value => { this.interested = value; }));
        this.subscriptions.add(registrationService.sessionPriorities$.subscribe(value => { this.interestedList = value.map(item => item.session); }));
        this.subscriptions.add(registrationService.sessions$.subscribe(value => { this.sessions = value; }));
    }

    ngOnDestroy(): void {
        this.subscriptions.unsubscribe();
    }

    scrollUp() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }

    scrollTo(session: ExchangeSession) {
        if (!this.sessionElements) {
            return;
        }

        for (const el of this.sessionElements) {
            if (el.session === session) {
                console.log(el);
                el.nativeElement.scrollIntoView({ behavior: 'smooth' });
                return;
            }
        }
    }

    updateList(pk: ExchangeSession['pk'], interested: boolean) {
        this.registrationService.update(pk, interested);
    }
}
