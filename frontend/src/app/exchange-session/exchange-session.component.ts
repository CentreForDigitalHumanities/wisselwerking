import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, ViewContainerRef } from '@angular/core';
import { ExchangeSession, Language } from '../models';
import { ProgramDetailLineComponent } from '../program-detail-line/program-detail-line.component';
import { faCheck } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'wsl-exchange-session',
    standalone: true,
    imports: [CommonModule, ProgramDetailLineComponent, FontAwesomeModule],
    templateUrl: './exchange-session.component.html',
    styleUrl: './exchange-session.component.scss'
})
export class ExchangeSessionComponent implements OnChanges {
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
    contact: string = '';
    nativeElement: HTMLElement;

    constructor(private readonly viewRef: ViewContainerRef) {
        this.nativeElement = this.viewRef.element.nativeElement;
    }

    clickInterested() {
        this.interestedChange.next(!this.interested);
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (!this.session) {
            return;
        }

        if (this.session.participantsMin === this.session.participantsMax) {
            this.participantCount = this.session.participantsMin.toString();
        } else if (this.session.participantsMax > 90) {
            this.participantCount = 'Onbeperkt';
        } else {
            this.participantCount = `${this.session.participantsMin} à ${this.session.participantsMax}`;
        }

        if (this.session.sessionCount > 90) {
            this.sessionCount = 'Onbeperkt';
        } else {
            this.sessionCount = this.session.sessionCount.toString();
        }

        this.title = this.session.title;

        const languages: Language[] = [];

        for (const description of this.session?.descriptions) {
            if (description.language == 'nl' || !this.title) {
                this.date = description.date;
                this.subtitle = description.subtitle
                this.intro = description.intro;
                this.program = description.program;
                this.location = description.location;
            }

            languages.push(description.language);
        }

        this.languages = languages.sort().map(lang => lang === 'nl' ? 'Nederlands' : 'Engels').join(' en ');
        this.contact = this.session.organizers.map(person => person.fullName).sort().join('; ');
    }
}
