import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CanvasAspectsComponent } from './canvas-aspects.component';

describe('CanvasAspectsComponent', () => {
  let component: CanvasAspectsComponent;
  let fixture: ComponentFixture<CanvasAspectsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CanvasAspectsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CanvasAspectsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
