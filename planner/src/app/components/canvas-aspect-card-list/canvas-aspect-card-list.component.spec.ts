import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CanvasAspectCardListComponent } from './canvas-aspect-card-list.component';

describe('CanvasAspectCardListComponent', () => {
  let component: CanvasAspectCardListComponent;
  let fixture: ComponentFixture<CanvasAspectCardListComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CanvasAspectCardListComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CanvasAspectCardListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
