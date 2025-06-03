import { Injectable } from '@angular/core';
import { Department, ExchangeSession } from '../models';
import { BehaviorSubject } from 'rxjs';
import { BackendService } from './backend.service';

export const MIN_PRIORITY = 1;
export const MAX_PRIORITY = 999;

export interface ExchangeSessionPriority {
    session: ExchangeSession,
    priority: number
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
        const interestedPriorities = <ExchangeSessionPriority[]>(<[any, boolean][]>Object.entries(interested)).filter(([_, value]) => value).map(([pk, _]) => {
            return {
                session: this.sessions.value.find(session => pk == session.pk && !session.full),
                // new sessions are placed at the end
                priority: this.interestedPriorities.value.find(priority => pk == priority.session.pk)?.priority ?? MAX_PRIORITY
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
