import { Component, EventEmitter, Input, OnChanges, OnDestroy, Output, SimpleChanges, ViewContainerRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { faCheck } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { TranslateDirective, TranslatePipe, TranslateService } from '@ngx-translate/core';
import { Subject, Subscription } from 'rxjs';
import { ExchangeSession, Language } from '../models';
import { ProgramDetailLineComponent } from '../program-detail-line/program-detail-line.component';

@Component({
    selector: 'wsl-exchange-session',
    standalone: true,
    imports: [CommonModule, ProgramDetailLineComponent, FontAwesomeModule, TranslateDirective, TranslatePipe],
    templateUrl: './exchange-session.component.html',
    styleUrl: './exchange-session.component.scss'
})
export class ExchangeSessionComponent implements OnChanges, OnDestroy {
    private subscription = new Subscription();
    private triggerUpdate = new Subject();
    faCheck = faCheck;

    @Input()
    session?: ExchangeSession;

    @Input()
    interested: boolean = false;

    @Output()
    interestedChange: EventEmitter<boolean> = new EventEmitter<boolean>();

    title: string = '';
    subtitle: string = '';
    intro: string = '';
    program: string = '';
    date: string = '';
    location: string = '';
    languages: string = '';
    participantCount: string = '';
    sessionCount: string = '';
    contact: { name: string, url: string }[] = [];
    nativeElement: HTMLElement;

    unlimitedText = '';
    dutchText = 'Nederlands';
    englishText = 'Engels';
    andText = 'en';

    constructor(private readonly viewRef: ViewContainerRef, private translateService: TranslateService) {
        this.nativeElement = this.viewRef.element.nativeElement;

        this.streamText('Onbeperkt', x => this.unlimitedText = x);
        this.streamText('Nederlands', x => this.dutchText = x);
        this.streamText('Engels', x => this.englishText = x);
        this.streamText('en', x => this.andText = x);

        this.subscription.add(
            this.translateService.onLangChange.subscribe(() => this.triggerUpdate.next({})));

        this.subscription.add(
            this.triggerUpdate.subscribe(() => {
                this.updateContent(<Language>this.translateService.getCurrentLang());
            }));
    }

    private streamText(key: string, assign: (text: string) => void) {
        this.subscription.add(
            this.translateService.stream(key).subscribe(text => assign(text)));

    }

    clickInterested() {
        this.interestedChange.next(!this.interested);
    }

    ngOnChanges(changes: SimpleChanges): void {
        this.triggerUpdate.next({});
    }

    private updateContent(language: Language) {
        if (!this.session) {
            return;
        }

        if (this.session.participantsMin === this.session.participantsMax) {
            this.participantCount = this.session.participantsMin.toString();
        } else if (this.session.participantsMax > 90) {
            this.participantCount = this.unlimitedText;
        } else {
            this.participantCount = `${this.session.participantsMin} à ${this.session.participantsMax}`;
        }

        if (this.session.sessionCount > 90) {
            this.sessionCount = this.unlimitedText;
        } else {
            this.sessionCount = this.session.sessionCount.toString();
        }

        this.title = this.session.title;

        const languages: Language[] = [];

        for (const description of this.session?.descriptions) {
            if (description.language == language || !this.title) {
                this.date = description.date;
                this.title = description.title;
                this.subtitle = description.subtitle
                this.intro = description.intro;
                this.program = description.program;
                this.location = description.location;
            }

            languages.push(description.language);
        }

        this.languages = languages.sort().map(lang => lang === 'nl' ? this.dutchText : this.englishText).join(` ${this.andText} `);
        this.contact = this.session.organizers.map(person => ({
            name: person.fullName,
            url: person.url
        })).sort((a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
    }

    ngOnDestroy(): void {
        this.subscription.unsubscribe();
    }
}
