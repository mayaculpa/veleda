import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import * as uuid from 'uuid';

import { CanvasAspectCardItemComponent } from './canvas-aspect-card-item.component';
import { CanvasAspect } from '../../models';

describe('CanvasAspectCardItemComponent', () => {
  let component: CanvasAspectCardItemComponent;
  let fixture: ComponentFixture<CanvasAspectCardItemComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [CanvasAspectCardItemComponent],
      schemas: [CUSTOM_ELEMENTS_SCHEMA]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CanvasAspectCardItemComponent);
    component = fixture.componentInstance;

    const expectedCanvasAspect: CanvasAspect = { id: uuid.v4(), type: 'some type' };
    component.canvasAspect = expectedCanvasAspect;

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
