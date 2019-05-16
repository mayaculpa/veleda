import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { StoreModule } from '@ngrx/store';

import { CanvasAspectsComponent } from './canvas-aspects.component';
import { featureReducer } from '../../root-store/canvas-aspect-store/reducer';

describe('CanvasAspectsComponent', () => {
  let component: CanvasAspectsComponent;
  let fixture: ComponentFixture<CanvasAspectsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [StoreModule.forRoot({}), StoreModule.forFeature('canvasAspect', featureReducer)],
      declarations: [CanvasAspectsComponent],
      schemas: [CUSTOM_ELEMENTS_SCHEMA]
    }).compileComponents();
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
