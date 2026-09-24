import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TranslateModule } from '@ngx-translate/core';

import { RegistrationService } from './registration.service';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

describe('RegistrationService', () => {
    let service: RegistrationService;

    beforeEach(() => {
        TestBed.configureTestingModule({
    imports: [TranslateModule.forRoot()],
    providers: [provideHttpClient(withInterceptorsFromDi()), provideHttpClientTesting()]
});
        service = TestBed.inject(RegistrationService);
    });

    it('should be created', () => {
        expect(service).toBeTruthy();
    });
});
