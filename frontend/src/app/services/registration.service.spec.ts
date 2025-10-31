import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TranslateModule } from '@ngx-translate/core';

import { RegistrationService } from './registration.service';

describe('RegistrationService', () => {
    let service: RegistrationService;

    beforeEach(() => {
        TestBed.configureTestingModule({
            imports: [HttpClientTestingModule, TranslateModule.forRoot()]
        });
        service = TestBed.inject(RegistrationService);
    });

    it('should be created', () => {
        expect(service).toBeTruthy();
    });
});
