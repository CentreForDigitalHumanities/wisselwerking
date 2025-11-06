import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, lastValueFrom } from 'rxjs';
import { TranslateService } from '@ngx-translate/core';
import { BackendService } from './backend.service';
import { Language } from '../models';

export interface LanguageInfo {
    current: Language;
    supported: {
        code: Language,
        name: string
    }[];
}

@Injectable({
    providedIn: 'root'
})
export class LanguageService {
    baseApiUrl = '/api';

    private current = new BehaviorSubject<Language>('nl');
    current$ = this.current.asObservable();

    constructor(private http: HttpClient, private backendService: BackendService, private translateService: TranslateService) {
    }

    async get(): Promise<LanguageInfo> {
        const response: {
            current: Language,
            supported: [Language, string][]
        } = await this.backendService.get('i18n', false);

        this.translateService.use(response.current);

        this.current.next(response.current);

        return {
            current: response.current,
            supported: response.supported.map(([code, name]) => ({ code, name }))
        };
    }

    /***
     * @throws ValidationErrors
     */
    async set(language: Language): Promise<void> {
        const response = lastValueFrom(this.http.post<void>(
            this.baseApiUrl + '/i18n/', {
            language
        }));

        try {
            this.translateService.use(language);
            this.current.next(language);
            return await response;
        } catch (error) {
            if (error instanceof HttpErrorResponse) {
                console.error(error.error);
            }
            throw error;
        }
    }
}
