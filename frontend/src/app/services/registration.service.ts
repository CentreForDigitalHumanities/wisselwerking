import { Injectable } from '@angular/core';
import { Department, ExchangeSession, Language } from '../models';
import { BehaviorSubject, combineLatestWith, map } from 'rxjs';
import { BackendService } from './backend.service';
import { LanguageService } from './language.service';

export const MIN_PRIORITY = 1;
export const MAX_PRIORITY = 999;

export interface ExchangeSessionPriority {
    session: ExchangeSession,
    priority: number
}

interface Exchange {
    "pk": number,
    "begin": number,
    "end": number,
    "enrollment_deadline": string, // yyyy-MM-dd
    "descriptions": {
        text: string,
        language: Language
    }[]
};

@Injectable({
    providedIn: 'root'
})
export class RegistrationService {
    private deadline = new BehaviorSubject<Date>(new Date());
    private description = new BehaviorSubject<string>('');
    private interested = new BehaviorSubject<{ [pk: ExchangeSession['pk']]: boolean }>({});
    private interestedPriorities = new BehaviorSubject<ExchangeSessionPriority[]>([]);
    private sessions = new BehaviorSubject<ExchangeSession[]>([]);

    deadline$ = this.deadline.asObservable();
    description$ = this.description.asObservable();
    interested$ = this.interested.asObservable();
    sessionPriorities$ = this.interestedPriorities.asObservable();
    sessions$ = this.sessions.pipe(
        combineLatestWith(this.languageService.current$),
        map(([sessions, language]) => {
            return this.sessionsByLanguage(sessions, language);
        }));

    constructor(private backend: BackendService, private languageService: LanguageService) {
        this.backend.get('current_exchange').then((exchange: Exchange) => {
            this.deadline.next(new Date(exchange.enrollment_deadline));
            this.languageService.current$.subscribe(language => {
                this.description.next(exchange.descriptions.find(d => d.language === language)?.text ?? '');
            });
        });
        this.backend.get('available_sessions').then(sessions => {
            this.sessions.next(<ExchangeSession[]>sessions);
        });
    }

    private sessionsByLanguage(sessions: ExchangeSession[], language: Language): ExchangeSession[] {
        return sessions
            .filter(session => session.descriptions.find(d => d.language === language))
            .map((session) => {
                // update title
                session.title = this.sessionTitle(session, language);
                session.sortTitle = (<string>session.title).replace(/[^A-Za-z]/g, '');
                return session;
            }).sort((a, b) => {
                if (a.sortTitle === b.sortTitle) {
                    return 0;
                } else if (a.sortTitle < b.sortTitle) {
                    return -1;
                } else {
                    return 1;
                }
            });
    }

    private sessionTitle(session: ExchangeSession, language: Language) {
        let title: string = '';
        for (const description of session.descriptions) {
            if (description.language == language || !title) {
                title = description.title;
            }
        }
        return title;
    }

    private departmentTitle(department: Department) {
        let title: string = '';
        for (const description of department.descriptions) {
            if (description.language == 'nl' || !title) {
                title = description.name;
            }
        }
        return title;
    }

    async departments() {
        const departments = await this.backend.get<Department[]>('departments');
        return departments.map(department => ({
            ...department,
            title: this.departmentTitle(department)
        }));
    }

    /**
     * Sort the priorities;
     * make sure they start from the minimum number;
     * make sure they do not exceed the maximum number;
     * make sure the step sizes are always 1
     */
    private cleanPriorities(interestedPriorities: ExchangeSessionPriority[]) {
        let cleaned = interestedPriorities.sort((a, b) => a.priority - b.priority);
        // if it is above 1 then the step size will be above 1; this way it is normalized
        // to start from the MIN_PRIORITY
        let currentPriority = 0;
        let correction = 0;
        for (const item of cleaned) {
            let updatedPriority = item.priority + correction;
            if (updatedPriority < MIN_PRIORITY) {
                updatedPriority = MIN_PRIORITY;
            } else {
                // step size is always 1
                updatedPriority = currentPriority + 1;
            }
            correction = updatedPriority - item.priority;
            item.priority = currentPriority = updatedPriority;
        }

        return cleaned;
    }

    update(pk: number, value: boolean) {
        const interested = { ...this.interested.value, [pk]: value };
        const interestedPriorities = <ExchangeSessionPriority[]>(<[any, boolean][]>Object.entries(interested))
            .filter(([_, x]) => x)
            .map(([x, _]) => {
                x = parseInt(x);
                return {
                    // 'surprise me' option
                    session: x === 0
                        ? { pk: x }
                        : this.sessions.value.find(session => x == session.pk && !session.full),
                    // new sessions are placed at the end
                    priority: this.interestedPriorities.value.find(priority => x == priority.session.pk)?.priority ?? MAX_PRIORITY
                };
            }).filter(session => !!session.session);

        this.interested.next(interested);
        this.interestedPriorities.next(this.cleanPriorities(interestedPriorities));
    }

    updatePriority(pk: number, priority: number) {
        const interestedPriorities = [...this.interestedPriorities.value.map(item => {
            if (item.session.pk == pk) {
                // place it just in front or behind the other item
                if (priority > item.priority) {
                    item.priority = priority + 0.1;
                } else {
                    item.priority = priority - 0.1;
                }
            }

            return item;
        })];

        this.interestedPriorities.next(this.cleanPriorities(interestedPriorities));
    }
}
