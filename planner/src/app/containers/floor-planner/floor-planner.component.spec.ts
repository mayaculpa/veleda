import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FloorPlannerComponent } from './floor-planner.component';

describe('FloorPlannerComponent', () => {
  let component: FloorPlannerComponent;
  let fixture: ComponentFixture<FloorPlannerComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FloorPlannerComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FloorPlannerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
