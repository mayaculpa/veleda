import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CanvasAspectCardItemComponent } from './canvas-aspect-card-item.component';

describe('CanvasAspectCardItemComponent', () => {
  let component: CanvasAspectCardItemComponent;
  let fixture: ComponentFixture<CanvasAspectCardItemComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CanvasAspectCardItemComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CanvasAspectCardItemComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
