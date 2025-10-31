import { Component, OnDestroy, QueryList, ViewChildren } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslateDirective } from '@ngx-translate/core';
import { combineLatestWith, Subscription } from 'rxjs';
import { faCheck, faCircleChevronUp } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { ExchangeSessionComponent } from "../exchange-session/exchange-session.component";
import { ExchangeSession } from '../models';
import { RegistrationService } from '../services/registration.service';
import { LanguageService } from '../services/language.service';

@Component({
    selector: 'wsl-overview',
    templateUrl: './overview.component.html',
    styleUrls: ['./overview.component.scss'],
    standalone: true,
    imports: [CommonModule, FontAwesomeModule, RouterLink, ExchangeSessionComponent, TranslateDirective]
})
export class OverviewComponent implements OnDestroy {
    subscriptions = new Subscription();

    faCheck = faCheck;
    faCircleChevronUp = faCircleChevronUp;
    interested: { [pk: ExchangeSession['pk']]: boolean } = {};
    interestedList: ExchangeSession[] = [];

    deadline?: string;
    sessions?: ExchangeSession[];

    overviewIntro = '';
    whenAndWhomTitle = '';
    whenAndWhomExplain = '';

    @ViewChildren(ExchangeSessionComponent)
    sessionElements?: QueryList<ExchangeSessionComponent>;

    constructor(private registrationService: RegistrationService, private languageService: LanguageService, activatedRoute: ActivatedRoute) {
        const lang = activatedRoute.snapshot.queryParams['lang'];
        if (['nl', 'en'].includes(lang)) {
            this.languageService.set(lang);
        }
        this.subscriptions.add(
            this.languageService.current$.pipe(
                combineLatestWith(this.registrationService.deadline$)).subscribe(([language, deadline]) => this.deadline = deadline.toLocaleString(language, {
                    weekday: 'long',
                    day: 'numeric',
                    year: 'numeric',
                    month: 'long'
                })));
        this.subscriptions.add(
            this.registrationService.description$.subscribe(description => {
                this.overviewIntro = '';
                this.whenAndWhomTitle = '';
                this.whenAndWhomExplain = '';
                let target: 'overviewIntro' | 'whenAndWhomExplain' = 'overviewIntro';
                for (const line of description.split('\n').map(l => l.trim())) {
                    if (line.startsWith('#')) {
                        this.whenAndWhomTitle = line.replace('#', '');
                        target = 'whenAndWhomExplain';
                    } else {
                        this[target] += line + '\n';
                    }
                }
            }));
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
                el.nativeElement.scrollIntoView({ behavior: 'smooth' });
                return;
            }
        }
    }

    updateList(pk: ExchangeSession['pk'], interested: boolean) {
        this.registrationService.update(pk, interested);
    }
}
