import { HttpClient, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { BackendService } from './backend.service';

describe('BackendService', () => {

  beforeEach(() => TestBed.configureTestingModule({ imports: [], providers: [provideHttpClient(withInterceptorsFromDi()), provideHttpClientTesting()] }));

    it('should be created', () => {
        const service = TestBed.inject(BackendService);
        expect(service).toBeTruthy();
    });
});
