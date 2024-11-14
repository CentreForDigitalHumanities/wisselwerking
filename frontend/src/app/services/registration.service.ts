import { Injectable } from '@angular/core';
import { Department, ExchangeSession } from '../models';
import { BehaviorSubject } from 'rxjs';
import { BackendService } from './backend.service';

export const MIN_PRIORITY = 1;
export const MAX_PRIORITY = 4;
export type PriorityValue = 1 | 2 | 3 | 4;

export interface ExchangeSessionPriority {
    session: ExchangeSession,
    priority: PriorityValue
}

@Injectable({
    providedIn: 'root'
})
export class RegistrationService {
    private interested = new BehaviorSubject<{ [pk: ExchangeSession['pk']]: boolean }>({});
    private interestedPriorities = new BehaviorSubject<ExchangeSessionPriority[]>([]);
    private sessions = new BehaviorSubject<ExchangeSession[]>([]);

    interested$ = this.interested.asObservable();
    sessionPriorities$ = this.interestedPriorities.asObservable();
    sessions$ = this.sessions.asObservable();

    constructor(private backend: BackendService) {
        this.backend.get('available_sessions').then(sessions => {
            this.sessions.next((<ExchangeSession[]>sessions.map((session: any) => {
                // add title
                session.title = this.sessionTitle(session);
                session.sortTitle = (<string>session.title).replace(/[^A-Za-z]/g, '');
                return session;
            })).sort((a, b) => {
                if (a.sortTitle === b.sortTitle) {
                    return 0;
                } else if (a.sortTitle < b.sortTitle) {
                    return -1;
                } else {
                    return 1;
                }
            }));
        });
    }

    private sessionTitle(session: ExchangeSession) {
        let title: string = '';
        for (const description of session.descriptions) {
            if (description.language == 'nl' || !title) {
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

    update(pk: number, value: boolean) {
        const interested = { ...this.interested.value, [pk]: value };
        const interestedPriorities = <ExchangeSessionPriority[]>(<[any, boolean][]>Object.entries(interested)).filter(([_, value]) => value).map(([pk, _]) => {
            return {
                session: this.sessions.value.find(session => pk == session.pk),
                priority: Math.max(MIN_PRIORITY, Math.min(MAX_PRIORITY, this.interestedPriorities.value.find(priority => pk == priority.session.pk)?.priority ?? Object.keys(interested).length))
            };
        }).filter(session => !!session.session);

        this.interested.next(interested);
        this.interestedPriorities.next(interestedPriorities);
    }

    updatePriority(pk: number, priority: number) {
        const maxPriority = Math.min(this.interestedPriorities.value.length, MAX_PRIORITY);
        const interestedPriorities = [...this.interestedPriorities.value.map(item => {
            if (item.session.pk == pk) {
                if (priority > maxPriority) {
                    priority = MIN_PRIORITY;
                } else if (priority < MIN_PRIORITY) {
                    priority = maxPriority;
                }
                item.priority = <PriorityValue>priority;
            }

            return item;
        })];

        this.interestedPriorities.next(interestedPriorities);
    }
}
