import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import * as uuid from 'uuid';

import { CanvasAspectCardListComponent } from './canvas-aspect-card-list.component';
import { CanvasAspect } from '../../models';

describe('CanvasAspectCardListComponent', () => {
  let component: CanvasAspectCardListComponent;
  let fixture: ComponentFixture<CanvasAspectCardListComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [CanvasAspectCardListComponent],
      schemas: [CUSTOM_ELEMENTS_SCHEMA]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CanvasAspectCardListComponent);
    component = fixture.componentInstance;

    const expectedCanvasAspects: CanvasAspect[] = [
      { id: uuid.v4(), type: 'first type' },
      { id: uuid.v4(), type: 'second type' }
    ];
    component.canvasAspects = expectedCanvasAspects;

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
