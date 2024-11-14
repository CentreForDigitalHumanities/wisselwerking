import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProgramDetailLineComponent } from './program-detail-line.component';

describe('ProgramDetailLineComponent', () => {
  let component: ProgramDetailLineComponent;
  let fixture: ComponentFixture<ProgramDetailLineComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProgramDetailLineComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ProgramDetailLineComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
