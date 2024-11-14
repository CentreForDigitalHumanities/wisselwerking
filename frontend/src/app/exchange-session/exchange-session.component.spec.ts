import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ExchangeSessionComponent } from './exchange-session.component';

describe('ExchangeSessionComponent', () => {
  let component: ExchangeSessionComponent;
  let fixture: ComponentFixture<ExchangeSessionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ExchangeSessionComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ExchangeSessionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
